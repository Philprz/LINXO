#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de notifications unifié pour Linxo Agent.

- Envoi d'emails (SMTP SSL/TLS)
- Envoi de SMS via OVH (API REST)
- Chargement de la config depuis linxo_agent.config.get_config() si disponible,
  sinon depuis les variables d'environnement.
- Journalisation standard via logging.
- Conçu pour passer Pylint : docstrings, types, pas d'exceptions trop générales,
  pas de variables globales cachées, pas de mutable default args, etc.

Note: Fournit en plus une façade optionnelle `send_budget_notification` qui
restitue la fonctionnalité V1 sans couplage fort. Elle fonctionne même si Jinja2
ou les formateurs ne sont pas installés (fallback texte).
"""

from __future__ import annotations

import logging
import os
import re
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGER = logging.getLogger("linxo.notifications")
if not LOGGER.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class NotificationError(Exception):
    """Erreur générique pour l'envoi des notifications."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _to_list(value: Union[str, Sequence[str], None]) -> List[str]:
    """Convertit une valeur en liste, nettoyée et sans doublons."""
    if value is None:
        return []
    if isinstance(value, str):
        items = [v.strip() for v in value.split(",") if v.strip()]
        return list(dict.fromkeys(items))
    return list(dict.fromkeys([str(v).strip() for v in value if str(v).strip()]))


def _env_bool(key: str, default: bool = False) -> bool:
    """Lit un booléen depuis l'environnement (1/true/yes/on)."""
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _safe_int(value: Union[str, int, None], default: int) -> int:
    """Convertit en int en sécurité."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class EmailSettings:
    """Paramètres d'envoi email."""
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_ssl: bool = True
    use_starttls: bool = False
    default_recipients: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OvhSmsSettings:
    """Paramètres OVH SMS (API v1, Europe)."""
    endpoint: str  # ex: "ovh-eu"
    application_key: str
    application_secret: str
    consumer_key: str
    account: str  # ex: "sms-xxxxxx-1"
    user: str  # ex: "sms-xxxxxx-1" (OVH_SERVICE_NAME)
    sender: str  # ex: "ITSPIRIT"
    default_recipients: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class NotificationConfig:
    """Configuration unifiée notifications."""
    emails: Optional[EmailSettings] = None
    ovh_sms: Optional[OvhSmsSettings] = None


def _try_import_get_config() -> Any:
    """
    Tente d'importer `get_config` depuis linxo_agent.config.
    Retourne l'objet fonction si disponible, sinon None.
    """
    try:
        from linxo_agent.config import get_config as _get_config  # type: ignore
        return _get_config
    except Exception:  # pylint: disable=broad-except
        return None


def _config_from_env() -> NotificationConfig:
    """
    Construit une config minimale depuis l'environnement.

    Variables supportées (emails) :
      - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_SENDER,
        SMTP_USE_SSL (bool), SMTP_USE_STARTTLS (bool),
        NOTIFICATION_EMAILS (liste séparée par des virgules)

    Variables supportées (OVH SMS) :
      - OVH_ENDPOINT (ex: ovh-eu)
      - OVH_APP_KEY, OVH_APP_SECRET, OVH_CONSUMER_KEY
      - OVH_SMS_ACCOUNT (ex: sms-xxxxxx-1)
      - OVH_SMS_SENDER (alphanum 3-11 chars)
      - OVH_SMS_RECIPIENTS (liste séparée par des virgules)
    """
    email_settings: Optional[EmailSettings] = None
    if os.getenv("SMTP_HOST") and os.getenv("SMTP_SENDER"):
        email_settings = EmailSettings(
            host=os.getenv("SMTP_HOST", ""),
            port=_safe_int(os.getenv("SMTP_PORT"), 465),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            sender=os.getenv("SMTP_SENDER", ""),
            use_ssl=_env_bool("SMTP_USE_SSL", True),
            use_starttls=_env_bool("SMTP_USE_STARTTLS", False),
            default_recipients=tuple(_to_list(os.getenv("NOTIFICATION_EMAILS"))),
        )

    ovh_settings: Optional[OvhSmsSettings] = None
    if os.getenv("OVH_ENDPOINT") and os.getenv("OVH_APP_KEY"):
        ovh_settings = OvhSmsSettings(
            endpoint=os.getenv("OVH_ENDPOINT", "ovh-eu"),
            application_key=os.getenv("OVH_APP_KEY", ""),
            application_secret=os.getenv("OVH_APP_SECRET", ""),
            consumer_key=os.getenv("OVH_CONSUMER_KEY", ""),
            account=os.getenv("OVH_SMS_ACCOUNT", ""),
            sender=os.getenv("OVH_SMS_SENDER", ""),
            default_recipients=tuple(_to_list(os.getenv("OVH_SMS_RECIPIENTS"))),
        )

    return NotificationConfig(emails=email_settings, ovh_sms=ovh_settings)


def load_notification_config() -> NotificationConfig:
    """
    Charge la configuration (priorité au module `linxo_agent.config` si présent).
    Fallback : variables d'environnement.
    """
    get_config = _try_import_get_config()
    if get_config is None:
        LOGGER.debug("get_config() indisponible, lecture depuis l'environnement")
        return _config_from_env()

    cfg = get_config()  # type: ignore[operator]

    def _get(mapping_or_obj: Any, key: str, default: Any = "") -> Any:
        if isinstance(mapping_or_obj, Mapping):
            return mapping_or_obj.get(key, default)
        return getattr(mapping_or_obj, key, default)

    # Email
    email_settings: Optional[EmailSettings] = None
    smtp_host = _get(cfg, "smtp_server", "") or os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_sender = _get(cfg, "smtp_email", "") or os.getenv("SMTP_SENDER", "")
    if smtp_sender:
        email_settings = EmailSettings(
            host=str(smtp_host),
            port=int(_get(cfg, "smtp_port", 587)),
            username=str(smtp_sender),
            password=str(_get(cfg, "smtp_password", "")),
            sender=str(smtp_sender),
            use_ssl=False,
            use_starttls=True,
            default_recipients=tuple(_get(cfg, "notification_emails", [])),
        )

    # OVH SMS (méthode email-to-SMS)
    ovh_settings: Optional[OvhSmsSettings] = None
    ovh_account = str(_get(cfg, "ovh_compte_sms", "") or _get(cfg, "ovh_user_api", ""))
    ovh_service_name = str(_get(cfg, "ovh_service_name", ""))
    if ovh_account:
        ovh_settings = OvhSmsSettings(
            endpoint="ovh-eu",
            application_key=ovh_account,  # OVH_USER_API
            application_secret=str(_get(cfg, "ovh_mot_de_passe_sms", "") or _get(cfg, "ovh_app_secret", "")),
            consumer_key="",  # Non utilisé pour email-to-SMS
            account=ovh_account,  # OVH_USER_API (premier champ)
            user=ovh_service_name,  # OVH_SERVICE_NAME (deuxième champ)
            sender=str(_get(cfg, "ovh_expediteur_sms", "") or _get(cfg, "sms_sender", "PhiPEREZ")),
            default_recipients=tuple(_get(cfg, "sms_recipients", [])),
        )

    return NotificationConfig(emails=email_settings, ovh_sms=ovh_settings)


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")  # E.164 approx


def _validate_emails(emails: Iterable[str]) -> List[str]:
    """Retourne la liste des emails valides (filtre silencieux)."""
    valid = []
    for addr in emails:
        addr_norm = addr.strip()
        if addr_norm and _EMAIL_RE.match(addr_norm):
            valid.append(addr_norm)
        else:
            LOGGER.warning("Adresse email invalide ignorée: %s", addr)
    return valid


def _validate_phones(phones: Iterable[str]) -> List[str]:
    """Retourne la liste des numéros valides en format proche E.164."""
    valid = []
    for num in phones:
        num_norm = num.strip().replace(" ", "")
        if num_norm.startswith("0") and not num_norm.startswith("+"):
            num_norm = "+33" + num_norm[1:]
        if _PHONE_RE.match(num_norm):
            valid.append(num_norm)
        else:
            LOGGER.warning("Numéro de téléphone invalide ignoré: %s", num)
    return valid


def _add_attachments(msg: MIMEMultipart, attachments: Iterable[Union[str, Path]]) -> None:
    """Ajoute des pièces jointes à un message MIME."""
    for item in attachments:
        path = Path(item)
        if not path.exists():
            LOGGER.warning("Pièce jointe introuvable: %s", path)
            continue
        with path.open("rb") as fobj:
            payload = MIMEApplication(fobj.read(), Name=path.name)
        payload["Content-Disposition"] = f'attachment; filename="{path.name}"'
        msg.attach(payload)


# ---------------------------------------------------------------------------
# Notification Manager
# ---------------------------------------------------------------------------

class NotificationManager:
    """
    Manager unifié pour emails et SMS.

    Parameters
    ----------
    config : Optional[NotificationConfig]
        Config explicite. Si None, on tente `load_notification_config()`.
    """

    def __init__(self, config: Optional[NotificationConfig] = None) -> None:
        self._config: NotificationConfig = config or load_notification_config()
        LOGGER.debug("NotificationManager initialisé: %s", self._config)

    # ------------------------------- EMAIL ---------------------------------

    def send_email(
        self,
        subject: str,
        body_text: str,
        recipients: Optional[Iterable[str]] = None,
        *,
        html_body: Optional[str] = None,
        attachments: Optional[Iterable[Union[str, Path]]] = None,
        reply_to: Optional[str] = None,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
    ) -> bool:
        """
        Envoie un email.

        Returns
        -------
        bool
            True si l'envoi a (semble) réussi, False sinon.
        """
        if self._config.emails is None:
            LOGGER.error("Configuration email indisponible.")
            return False

        settings = self._config.emails
        to_list = _validate_emails(recipients or settings.default_recipients)
        cc_list = _validate_emails(cc or [])
        bcc_list = _validate_emails(bcc or [])

        if not to_list and not cc_list and not bcc_list:
            LOGGER.error("Aucun destinataire email valide.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.sender
        msg["To"] = ", ".join(to_list)
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        if reply_to:
            msg.add_header("Reply-To", reply_to)

        msg.attach(MIMEText(body_text or "", "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        if attachments:
            _add_attachments(msg, attachments)

        recipients_all = list(dict.fromkeys([*to_list, *cc_list, *bcc_list]))

        try:
            if settings.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(settings.host, settings.port, context=context) as smtp:
                    if settings.username:
                        smtp.login(settings.username, settings.password)
                    smtp.sendmail(settings.sender, recipients_all, msg.as_string())
            else:
                with smtplib.SMTP(settings.host, settings.port) as smtp:
                    if settings.use_starttls:
                        context = ssl.create_default_context()
                        smtp.starttls(context=context)
                    if settings.username:
                        smtp.login(settings.username, settings.password)
                    smtp.sendmail(settings.sender, recipients_all, msg.as_string())

            LOGGER.info("Email envoyé à %s", recipients_all)
            return True

        except smtplib.SMTPException as exc:
            LOGGER.exception("Echec envoi email (SMTPException) : %s", exc)
            return False

    # ------------------------------- SMS OVH -------------------------------

    def send_sms_ovh(
        self,
        message: str,
        recipients: Optional[Iterable[str]] = None,
        *,
        no_stop_clause: bool = False,
    ) -> bool:
        """
        Envoie un SMS via OVH (méthode email-to-SMS).

        Notes
        -----
        - Utilise la méthode email2sms@ovh.net
        - Le message est automatiquement tronqué à 160 caractères
        - Format du sujet: compte:utilisateur:password:expediteur:destinataire
        """
        if self._config.ovh_sms is None:
            LOGGER.error("Configuration OVH SMS indisponible.")
            return False

        if self._config.emails is None:
            LOGGER.error("Configuration email requise pour l'envoi SMS via OVH.")
            return False

        settings = self._config.ovh_sms
        email_settings = self._config.emails
        to_list = _validate_phones(recipients or settings.default_recipients)
        if not to_list:
            LOGGER.error("Aucun destinataire SMS valide.")
            return False

        # Tronquer le message si nécessaire
        final_message = message.strip()
        if len(final_message) > 160:
            LOGGER.warning("Message > 160 chars, tronqué.")
            final_message = final_message[:157] + "..."

        # Envoyer un SMS à chaque destinataire via email2sms
        success_count = 0
        for phone in to_list:
            try:
                # Format du sujet pour OVH: compte:utilisateur:password:expediteur:destinataire
                # OVH_USER_API:OVH_SERVICE_NAME:OVH_APP_SECRET:SMS_SENDER:SMS_RECIPIENT
                subject = f"{settings.account}:{settings.user}:{settings.application_secret}:{settings.sender}:{phone}"

                msg = MIMEMultipart()
                msg["Subject"] = subject
                msg["From"] = email_settings.sender
                msg["To"] = "email2sms@ovh.net"

                body = MIMEText(final_message, "plain", "utf-8")
                msg.attach(body)

                LOGGER.info("Envoi SMS via OVH à %s...", phone)

                if email_settings.use_ssl:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(email_settings.host, email_settings.port, context=context) as smtp:
                        if email_settings.username:
                            smtp.login(email_settings.username, email_settings.password)
                        smtp.sendmail(email_settings.sender, "email2sms@ovh.net", msg.as_string())
                else:
                    with smtplib.SMTP(email_settings.host, email_settings.port) as smtp:
                        if email_settings.use_starttls:
                            context = ssl.create_default_context()
                            smtp.starttls(context=context)
                        if email_settings.username:
                            smtp.login(email_settings.username, email_settings.password)
                        smtp.sendmail(email_settings.sender, "email2sms@ovh.net", msg.as_string())

                LOGGER.info("SMS envoyé à %s", phone)
                success_count += 1

            except smtplib.SMTPException as exc:
                LOGGER.error("Echec SMS pour %s: %s", phone, exc)
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.error("Erreur inattendue SMS pour %s: %s", phone, exc)

        return success_count > 0

    # -------------------------- Façades & budget ---------------------------

    def notify_quick(
        self,
        subject: str,
        message: str,
        *,
        email: bool = True,
        sms: bool = False,
        html_body: Optional[str] = None,
        attachments: Optional[Iterable[Union[str, Path]]] = None,
    ) -> Tuple[bool, bool]:
        """
        Notifie rapidement par email et/ou SMS.

        Returns
        -------
        (email_ok, sms_ok) : Tuple[bool, bool]
        """
        email_ok = True
        sms_ok = True

        if email:
            email_ok = self.send_email(
                subject=subject,
                body_text=message,
                html_body=html_body,
                attachments=attachments,
            )

        if sms:
            sms_ok = self.send_sms_ovh(message)

        return email_ok, sms_ok

    # --- Optionnel : réintègre la fonction V1 de notification budget ---

    def send_budget_notification(
        self,
        analysis_result: Mapping[str, Any],
        report_index: Any = None,
    ) -> Mapping[str, Any]:
        """
        Envoie les notifications (email + SMS) pour le rapport budgétaire.

        - Utilise si dispo: formater_sms_v2 / formater_email_html_v2
        - Si `report_index` fourni et Jinja2 dispo, tente un HTML avec lien index
        - Fallback texte sinon
        """
        total_depenses = float(
            analysis_result.get("total_variables", 0) or 0
        )  # type: ignore[arg-type]
        budget_max = float(analysis_result.get("budget_max", 0) or 0)  # type: ignore[arg-type]
        reste = budget_max - total_depenses
        pct = (total_depenses / budget_max * 100) if budget_max > 0 else 0.0

        # SMS via formateur si dispo
        sms_msg = None
        try:
            from report_formatter_v2 import formater_sms_v2  # type: ignore
            sms_msg = formater_sms_v2(total_depenses, budget_max, reste, pct)
        except Exception:  # pylint: disable=broad-except
            sms_msg = (
                f"Budget: {total_depenses:.0f}/{budget_max:.0f}€ "
                f"({pct:.0f}%), reste {reste:.0f}€"
            )

        # Sujet
        from datetime import datetime as _dt
        if reste < 0:
            subject = f"🔴 ALERTE Budget - Dépassement de {abs(reste):.0f}€"
        elif pct >= 80:
            subject = f"🟠 Budget à {pct:.0f}% - Attention"
        else:
            subject = f"🟢 Rapport Budget - {_dt.now().strftime('%d/%m/%Y')}"

        # Corps HTML:
        html_body: Optional[str] = None
        try:
            if report_index is not None:
                # Essai rendu Jinja2 si présent
                from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
                import os as _os

                templates_dir = Path(__file__).parent.parent / "templates" / "email"
                env = Environment(
                    loader=FileSystemLoader(templates_dir),
                    autoescape=select_autoescape(["html", "xml"]),
                )
                template = env.get_template("daily_summary.html.j2")

                base_url = _os.getenv("REPORTS_BASE_URL", "")
                index_url = "#"
                if base_url:
                    report_date = getattr(report_index, "report_date", "")
                    index_relative = f"/reports/{report_date}/index.html"
                    index_url = f"{base_url.rstrip('/')}{index_relative}"
                    signing_key = _os.getenv("REPORTS_SIGNING_KEY")
                    if signing_key:
                        # token si présent
                        try:
                            from reports import generate_token  # type: ignore
                            token = generate_token(index_relative, signing_key)
                            index_url = f"{index_url}?t={token}"
                        except Exception:  # pylint: disable=broad-except
                            pass

                total_fixes = float(
                    analysis_result.get("total_fixes", 0) or 0
                )  # type: ignore[arg-type]
                try:
                    # si la config expose les dépenses fixes de référence
                    cfg = _try_import_get_config()
                    depenses_fixes_ref = []  # type: ignore[assignment]
                    if cfg:
                        c = cfg()  # type: ignore[operator]
                        depenses_fixes_ref = getattr(
                            c, "depenses_data", {}
                        ).get("depenses_fixes", [])  # type: ignore[assignment, index]
                    budget_fixes_prevu = sum(
                        float(d.get("montant", 0) or 0)  # type: ignore[call-arg]
                        for d in depenses_fixes_ref
                    )
                except Exception:  # pylint: disable=broad-except
                    budget_fixes_prevu = 3271.0  # Fallback (mise à jour 2025)

                import calendar
                now = _dt.now()
                avancement_mois = (
                    now.day / calendar.monthrange(now.year, now.month)[1]
                ) * 100.0
                couleur_barre_variables = "#28a745"
                if reste < 0:
                    couleur_barre_variables = "#dc3545"
                elif pct > avancement_mois + 10:
                    couleur_barre_variables = "#fd7e14"

                pourcentage_fixes = (
                    (total_fixes / budget_fixes_prevu * 100)
                    if budget_fixes_prevu > 0
                    else 0
                )
                couleur_barre_fixes = "#28a745"
                if pourcentage_fixes > 100:
                    couleur_barre_fixes = "#dc3545"
                elif pourcentage_fixes > 90:
                    couleur_barre_fixes = "#fd7e14"

                html_body = template.render(
                    report_date=getattr(report_index, "report_date", ""),
                    total_variables=total_depenses,
                    total_fixes=total_fixes,
                    budget_max=budget_max,
                    budget_fixes_prevu=int(budget_fixes_prevu),
                    reste=reste,
                    pourcentage=pct,
                    pourcentage_fixes=pourcentage_fixes,
                    couleur_barre_variables=couleur_barre_variables,
                    couleur_barre_fixes=couleur_barre_fixes,
                    families=getattr(report_index, "families", []),
                    grand_total=getattr(report_index, "grand_total", 0),
                    index_url=index_url,
                )
            else:
                # Formateur HTML si dispo
                try:
                    from report_formatter_v2 import formater_email_html_v2  # type: ignore
                    html_body = formater_email_html_v2(analysis_result, budget_max, None)
                except Exception:  # pylint: disable=broad-except
                    html_body = None
        except Exception:  # pylint: disable=broad-except
            html_body = None

        csv_path = analysis_result.get("csv_path")
        attachments = [csv_path] if isinstance(csv_path, (str, Path)) else None

        sms_ok = self.send_sms_ovh(sms_msg) if sms_msg else False
        email_ok = self.send_email(
            subject=subject,
            body_text=(
                html_body
                or f"Budget variables: {total_depenses:.0f}€ / "
                f"{budget_max:.0f}€ (reste {reste:.0f}€)"
            ),
            html_body=html_body,
            attachments=attachments,
        )

        return {"email": email_ok, "sms": sms_ok}

    def send_technical_alert(
        self,
        error_type: str,
        error_message: str,
        alert_email: str = "phiperez@gmail.com",
    ) -> bool:
        """
        Envoie une alerte technique en cas de problème avec le système.

        Args:
            error_type: Type d'erreur (ex: "CSV non téléchargé", "Erreur d'analyse")
            error_message: Message détaillé de l'erreur
            alert_email: Email de destination pour l'alerte (par défaut phiperez@gmail.com)

        Returns:
            bool: True si l'alerte a été envoyée
        """
        from datetime import datetime as _dt

        subject = f"🔴 ALERTE TECHNIQUE - Linxo Agent - {error_type}"

        body_text = f"""ALERTE TECHNIQUE - LINXO AGENT
{'=' * 80}

Type d'erreur: {error_type}
Date/Heure: {_dt.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 80}
DESCRIPTION DE L'ERREUR
{'=' * 80}

{error_message}

{'=' * 80}
ACTION REQUISE
{'=' * 80}

Le système Linxo Agent nécessite une intervention technique.
Veuillez vérifier les logs et corriger le problème dès que possible.

Pour diagnostiquer:
1. Connectez-vous au VPS
2. Consultez les logs: ~/LINXO/logs/daily_report_*.log
3. Vérifiez que le téléchargement CSV fonctionne
4. Testez manuellement: python linxo_agent/run_analysis.py

---
Cette alerte a été générée automatiquement par Linxo Agent
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .alert-box {{
            background-color: #fee;
            border-left: 4px solid #dc3545;
            padding: 20px;
            margin: 20px 0;
        }}
        .error-type {{
            font-size: 24px;
            font-weight: bold;
            color: #dc3545;
            margin-bottom: 10px;
        }}
        .datetime {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .error-message {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
            font-family: monospace;
            white-space: pre-wrap;
        }}
        .action-required {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
        .steps {{
            margin-left: 20px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="alert-box">
        <div class="error-type">🔴 ALERTE TECHNIQUE - LINXO AGENT</div>
        <div class="datetime">Date/Heure: {_dt.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>

    <h2>Type d'erreur</h2>
    <p><strong>{error_type}</strong></p>

    <h2>Description de l'erreur</h2>
    <div class="error-message">{error_message}</div>

    <div class="action-required">
        <h2>⚠️ Action requise</h2>
        <p>Le système Linxo Agent nécessite une intervention technique.</p>
        <p><strong>Pour diagnostiquer:</strong></p>
        <ol class="steps">
            <li>Connectez-vous au VPS</li>
            <li>Consultez les logs: <code>~/LINXO/logs/daily_report_*.log</code></li>
            <li>Vérifiez que le téléchargement CSV fonctionne</li>
            <li>Testez manuellement: <code>python linxo_agent/run_analysis.py</code></li>
        </ol>
    </div>

    <div class="footer">
        Cette alerte a été générée automatiquement par Linxo Agent
    </div>
</body>
</html>"""

        try:
            result = self.send_email(
                subject=subject,
                body_text=body_text,
                html_body=html_body,
                recipients=[alert_email],
            )

            if result:
                LOGGER.info("Alerte technique envoyée à %s", alert_email)
            else:
                LOGGER.error("Échec de l'envoi de l'alerte technique à %s", alert_email)

            return result

        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception("Erreur lors de l'envoi de l'alerte technique: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Script de test manuel
# ---------------------------------------------------------------------------

def _example_usage() -> None:
    """Exemple d'utilisation locale, sans dépendre de l'appli principale."""
    cfg = load_notification_config()
    manager = NotificationManager(cfg)

    LOGGER.info("Config email: %s", bool(cfg.emails))
    LOGGER.info("Config OVH SMS: %s", bool(cfg.ovh_sms))

    if cfg.emails:
        LOGGER.info("Envoi email de test…")
        ok = manager.send_email(
            subject="[Linxo Agent] Test notifications",
            body_text="Ceci est un test d'email envoyé par le module notifications.",
        )
        LOGGER.info("Email test: %s", "OK" if ok else "ECHEC")

    if cfg.ovh_sms:
        LOGGER.info("Envoi SMS de test…")
        ok = manager.send_sms_ovh("Test Linxo Agent — tout roule ?")
        LOGGER.info("SMS test: %s", "OK" if ok else "ECHEC")


if __name__ == "__main__":
    _example_usage()
