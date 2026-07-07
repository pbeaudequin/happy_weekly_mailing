"""Script principal pour envoyer les emails récapitulatifs du calendrier."""

import os
import sys
import netrc
from pathlib import Path
from dotenv import load_dotenv

from .calendar_fetcher import CalendarFetcher
from .email_generator import EmailGenerator
from .email_sender import EmailSender
from .website_recap_fetcher import WebsiteRecapFetcher


def load_netrc_credentials(host: str = "smtp.gmail.com"):
    """
    Charge les identifiants depuis le fichier .netrc.

    Args:
        host: Nom d'hôte SMTP pour lequel récupérer les identifiants

    Returns:
        Tuple (login, password) ou (None, None) si non trouvé
    """
    try:
        netrc_path = Path.home() / '.netrc'
        if not netrc_path.exists():
            return None, None

        authenticators = netrc.netrc(str(netrc_path))
        auth = authenticators.authenticators(host)

        if auth:
            login, account, password = auth
            return login, password

        return None, None

    except (netrc.NetrcParseError, FileNotFoundError, KeyError):
        return None, None


def load_config():
    """
    Charge la configuration depuis les variables d'environnement.

    Returns:
        Dictionnaire avec la configuration
    """
    # Chercher le fichier .env dans le répertoire du projet
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)

    # Récupérer le host SMTP (par défaut Gmail)
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')

    # Essayer de charger les identifiants depuis .netrc en priorité
    netrc_login, netrc_password = load_netrc_credentials(smtp_host)

    # Utiliser netrc si disponible, sinon les variables d'environnement
    smtp_user = netrc_login or os.getenv('SMTP_USER')
    smtp_password = netrc_password or os.getenv('SMTP_PASSWORD')

    config = {
        # Configuration du calendrier
        'calendar_id': os.getenv('CALENDAR_ID', 'happy.rouret@gmail.com'),
        'timezone': os.getenv('TIMEZONE', 'Europe/Paris'),
        'days_ahead': int(os.getenv('DAYS_AHEAD', '14')),
        'website_recap_enabled': os.getenv('WEBSITE_RECAP_ENABLED', 'true').lower() == 'true',
        'website_recap_base_url': os.getenv('WEBSITE_RECAP_BASE_URL', 'https://www.happy-au-rouret.fr'),
        'website_recap_year': int(os.getenv('WEBSITE_RECAP_YEAR')) if os.getenv('WEBSITE_RECAP_YEAR') else None,
        'website_recap_limit': int(os.getenv('WEBSITE_RECAP_LIMIT', '3')),

        # Configuration de l'email
        'template_name': os.getenv('EMAIL_TEMPLATE', 'design_classique'),
        'email_subject': os.getenv('EMAIL_SUBJECT', 'Happy au Rouret - Prochains événements'),
        'from_name': os.getenv('FROM_NAME', 'Happy au Rouret'),

        # Configuration SMTP
        'smtp_host': smtp_host,
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'smtp_user': smtp_user,
        'smtp_password': smtp_password,
        'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        'using_netrc': bool(netrc_login and netrc_password),

        # Destinataires
        'to_addresses': os.getenv('TO_ADDRESSES', '').split(','),
    }

    # Nettoyer les adresses email (supprimer les espaces)
    config['to_addresses'] = [addr.strip() for addr in config['to_addresses'] if addr.strip()]

    return config


def validate_config(config):
    """
    Valide la configuration.

    Args:
        config: Dictionnaire de configuration

    Returns:
        Tuple (bool, str) : (est_valide, message_erreur)
    """
    required_fields = ['smtp_host', 'smtp_user', 'smtp_password']
    missing_fields = [field for field in required_fields if not config.get(field)]

    if missing_fields:
        return False, f"Configuration incomplète. Champs manquants : {', '.join(missing_fields)}"

    if not config['to_addresses']:
        return False, "Aucun destinataire spécifié (TO_ADDRESSES)"

    return True, ""


def main():
    """Point d'entrée principal du script."""
    print("=" * 60)
    print("  Happy au Rouret - Envoi d'email récapitulatif")
    print("=" * 60)
    print()

    # Charger la configuration
    print("📋 Chargement de la configuration...")
    config = load_config()

    # Valider la configuration
    is_valid, error_msg = validate_config(config)
    if not is_valid:
        print(f"✗ Erreur : {error_msg}")
        print()
        if not config.get('using_netrc'):
            print("💡 Vous pouvez configurer les identifiants SMTP de deux façons :")
            print("   1. Fichier .netrc (recommandé) - Voir README.md pour les instructions")
            print("   2. Fichier .env - Voir .env.example pour un exemple")
        return 1

    print(f"   Calendrier : {config['calendar_id']}")
    print(f"   Template : {config['template_name']}")
    print(f"   Période : {config['days_ahead']} jours")
    print(f"   Destinataires : {len(config['to_addresses'])} adresse(s)")
    if config.get('using_netrc'):
        print(f"   Authentification : .netrc ({config['smtp_host']})")
    else:
        print(f"   Authentification : Variables d'environnement")
    print()

    # Récupérer les événements
    print("📅 Récupération des événements...")
    try:
        fetcher = CalendarFetcher(config['calendar_id'], config['timezone'])
        events = fetcher.fetch_events(config['days_ahead'])

        if not events:
            print("   Aucun événement trouvé pour la période spécifiée.")
            print()
            print("ℹ️  Aucun email ne sera envoyé.")
            return 0

        print(f"   ✓ {len(events)} événement(s) trouvé(s)")
        for event in events:
            print(f"      - {event['title']} ({event['start_datetime'].strftime('%d/%m/%Y')})")
        print()

    except Exception as e:
        print(f"   ✗ Erreur : {e}")
        return 1

    # Formater les événements pour l'email
    print("🎨 Génération de l'email...")
    try:
        formatted_events = [fetcher.format_event_for_email(event) for event in events]

        recap_items = []
        if config['website_recap_enabled']:
            print("🌐 Récupération des dernières nouvelles du site...")
            try:
                recap_fetcher = WebsiteRecapFetcher(
                    base_url=config['website_recap_base_url'],
                    timezone=config['timezone'],
                    year=config['website_recap_year'],
                )
                recap_items = recap_fetcher.fetch_latest(config['website_recap_limit'])
                print(f"   ✓ {len(recap_items)} contenu(s) récent(s) trouvé(s)")
            except Exception as e:
                print(f"   ⚠️  Recap site indisponible : {e}")

        generator = EmailGenerator(config['template_name'])
        html_content = generator.generate(formatted_events, recap_items)

        print(f"   ✓ Email généré ({len(html_content)} caractères)")
        print()

    except Exception as e:
        print(f"   ✗ Erreur : {e}")
        return 1

    # Envoyer l'email
    print("📧 Envoi de l'email...")
    try:
        sender = EmailSender(
            smtp_host=config['smtp_host'],
            smtp_port=config['smtp_port'],
            smtp_user=config['smtp_user'],
            smtp_password=config['smtp_password'],
            use_tls=config['use_tls']
        )

        success = sender.send_email(
            to_addresses=config['to_addresses'],
            subject=config['email_subject'],
            html_content=html_content,
            from_name=config['from_name']
        )

        if success:
            print()
            print("=" * 60)
            print("  ✓ Email envoyé avec succès !")
            print("=" * 60)
            return 0
        else:
            print()
            print("=" * 60)
            print("  ✗ Échec de l'envoi de l'email")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"   ✗ Erreur : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
