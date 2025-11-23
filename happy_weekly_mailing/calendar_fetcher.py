"""Module pour récupérer les événements du calendrier Google."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from urllib.parse import quote
import requests
import pytz
from icalendar import Calendar


class CalendarFetcher:
    """Récupère les événements d'un calendrier Google via iCal."""

    def __init__(self, calendar_id: str, timezone: str = "Europe/Paris"):
        """
        Initialise le fetcher de calendrier.

        Args:
            calendar_id: ID du calendrier Google (ex: happy.rouret@gmail.com)
            timezone: Fuseau horaire pour les événements
        """
        self.calendar_id = calendar_id
        self.timezone = pytz.timezone(timezone)
        self.ical_url = f"https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics"

    def fetch_events(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Récupère les événements des prochains jours.

        Args:
            days_ahead: Nombre de jours à récupérer à partir d'aujourd'hui

        Returns:
            Liste des événements avec leurs détails
        """
        try:
            response = requests.get(self.ical_url, timeout=10)
            response.raise_for_status()

            cal = Calendar.from_ical(response.content)
            events = []

            now = datetime.now(self.timezone)
            end_date = now + timedelta(days=days_ahead)

            for component in cal.walk():
                if component.name == "VEVENT":
                    event = self._parse_event(component, now, end_date)
                    if event:
                        events.append(event)

            # Trier les événements par date
            events.sort(key=lambda x: x['start_datetime'])

            return events

        except requests.RequestException as e:
            raise Exception(f"Erreur lors de la récupération du calendrier : {e}")
        except Exception as e:
            raise Exception(f"Erreur lors du parsing du calendrier : {e}")

    def _parse_event(
        self,
        event_component: Any,
        start_filter: datetime,
        end_filter: datetime
    ) -> Dict[str, Any] | None:
        """
        Parse un événement iCal.

        Args:
            event_component: Composant VEVENT de l'événement
            start_filter: Date de début du filtre
            end_filter: Date de fin du filtre

        Returns:
            Dictionnaire avec les informations de l'événement ou None si hors période
        """
        try:
            start_dt = event_component.get('dtstart').dt

            # Gérer les événements "all-day" (date seulement, pas datetime)
            if isinstance(start_dt, datetime):
                if start_dt.tzinfo is None:
                    start_dt = self.timezone.localize(start_dt)
                else:
                    start_dt = start_dt.astimezone(self.timezone)
            else:
                # Pour les événements "all-day", créer un datetime à minuit
                start_dt = self.timezone.localize(
                    datetime.combine(start_dt, datetime.min.time())
                )

            # Filtrer les événements hors de la période
            if start_dt < start_filter or start_dt > end_filter:
                return None

            # Récupérer l'heure de fin si disponible
            end_dt = event_component.get('dtend')
            if end_dt:
                end_dt = end_dt.dt
                if isinstance(end_dt, datetime):
                    if end_dt.tzinfo is None:
                        end_dt = self.timezone.localize(end_dt)
                    else:
                        end_dt = end_dt.astimezone(self.timezone)

            # Extraire les informations
            summary = str(event_component.get('summary', 'Sans titre'))
            description = str(event_component.get('description', ''))
            location = str(event_component.get('location', ''))

            return {
                'title': summary,
                'description': description,
                'location': location if location else 'Lieu à confirmer',
                'start_datetime': start_dt,
                'end_datetime': end_dt,
                'is_all_day': not isinstance(event_component.get('dtstart').dt, datetime)
            }

        except Exception as e:
            print(f"Erreur lors du parsing d'un événement : {e}")
            return None

    def format_event_for_email(self, event: Dict[str, Any]) -> Dict[str, str]:
        """
        Formate un événement pour l'affichage dans l'email.

        Args:
            event: Événement à formater

        Returns:
            Dictionnaire avec les champs formatés pour le template
        """
        start_dt = event['start_datetime']

        # Déterminer le format d'heure
        if event['is_all_day']:
            time_str = "Toute la journée"
        elif event['end_datetime']:
            time_str = f"{start_dt.strftime('%H:%M')} - {event['end_datetime'].strftime('%H:%M')}"
        else:
            time_str = start_dt.strftime('%H:%M')

        # Formater la description si présente
        description_html = ""
        if event['description'] and event['description'].strip():
            description_html = f'<p style="color: #777; font-size: 14px; margin: 8px 0 0 0; line-height: 1.5;">{event["description"]}</p>'

        # Choisir une couleur d'événement (rotation entre plusieurs couleurs)
        colors = ['#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff']
        color_index = hash(event['title']) % len(colors)

        # Choisir une icône selon le type d'événement (basé sur des mots-clés)
        icon = '🎉'
        title_lower = event['title'].lower()
        if 'repas' in title_lower or 'déjeuner' in title_lower or 'dîner' in title_lower:
            icon = '🍽️'
        elif 'randonn' in title_lower or 'marche' in title_lower or 'balade' in title_lower:
            icon = '🥾'
        elif 'jardin' in title_lower or 'potager' in title_lower:
            icon = '🌱'
        elif 'sortie' in title_lower or 'visite' in title_lower:
            icon = '🚌'
        elif 'réunion' in title_lower or 'assemblée' in title_lower:
            icon = '📋'

        # Générer les liens pour ajouter au calendrier
        calendar_links = self._generate_calendar_links(event)

        return {
            'day': start_dt.strftime('%d'),
            'month': self._get_french_month(start_dt.month),
            'month_short': self._get_french_month_short(start_dt.month),
            'time': time_str,
            'title': event['title'],
            'location': event['location'],
            'description': description_html,
            'event_color': colors[color_index],
            'icon': icon,
            'add_to_google': calendar_links['google'],
            'add_to_outlook': calendar_links['outlook'],
            'add_to_yahoo': calendar_links['yahoo'],
            'add_to_ical': calendar_links['ical']
        }

    @staticmethod
    def _get_french_month(month_num: int) -> str:
        """Retourne le nom du mois en français."""
        months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        return months[month_num - 1]

    @staticmethod
    def _get_french_month_short(month_num: int) -> str:
        """Retourne le nom court du mois en français."""
        months = [
            "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
            "Juil", "Août", "Sep", "Oct", "Nov", "Déc"
        ]
        return months[month_num - 1]

    @staticmethod
    def _generate_calendar_links(event: Dict[str, Any]) -> Dict[str, str]:
        """
        Génère les liens pour ajouter l'événement aux différents calendriers.

        Args:
            event: Événement avec start_datetime, end_datetime, title, description, location

        Returns:
            Dictionnaire avec les liens pour différents calendriers
        """
        start_dt = event['start_datetime']
        end_dt = event.get('end_datetime')

        # Si pas d'heure de fin, utiliser +2h par défaut (sauf pour événements "all day")
        if not end_dt:
            if event.get('is_all_day'):
                end_dt = start_dt + timedelta(days=1)
            else:
                end_dt = start_dt + timedelta(hours=2)

        # Format pour Google Calendar et autres : YYYYMMDDTHHmmssZ (UTC)
        # Pour les événements "all day", utiliser le format YYYYMMDD
        if event.get('is_all_day'):
            start_str = start_dt.strftime('%Y%m%d')
            end_str = end_dt.strftime('%Y%m%d')
        else:
            # Convertir en UTC pour les liens calendrier
            start_utc = start_dt.astimezone(pytz.UTC)
            end_utc = end_dt.astimezone(pytz.UTC)
            start_str = start_utc.strftime('%Y%m%dT%H%M%SZ')
            end_str = end_utc.strftime('%Y%m%dT%H%M%SZ')

        # Encoder les paramètres
        title = quote(event['title'])
        description = quote(event.get('description', ''))
        location = quote(event.get('location', ''))

        # Google Calendar
        google_url = (
            f"https://calendar.google.com/calendar/render?"
            f"action=TEMPLATE"
            f"&text={title}"
            f"&dates={start_str}/{end_str}"
            f"&details={description}"
            f"&location={location}"
        )

        # Outlook.com / Office 365
        outlook_url = (
            f"https://outlook.live.com/calendar/0/deeplink/compose?"
            f"subject={title}"
            f"&startdt={start_str}"
            f"&enddt={end_str}"
            f"&body={description}"
            f"&location={location}"
            f"&path=/calendar/action/compose"
            f"&rru=addevent"
        )

        # Yahoo Calendar
        yahoo_url = (
            f"https://calendar.yahoo.com/?"
            f"v=60"
            f"&title={title}"
            f"&st={start_str}"
            f"&et={end_str}"
            f"&desc={description}"
            f"&in_loc={location}"
        )

        # Lien iCal/ICS universel (on génère un lien Google qui peut être utilisé par tous)
        ical_url = google_url

        return {
            'google': google_url,
            'outlook': outlook_url,
            'yahoo': yahoo_url,
            'ical': ical_url
        }
