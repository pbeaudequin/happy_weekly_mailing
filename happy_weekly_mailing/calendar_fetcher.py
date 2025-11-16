"""Module pour récupérer les événements du calendrier Google."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
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

    def fetch_events(self, days_ahead: int = 14) -> List[Dict[str, Any]]:
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

        return {
            'day': start_dt.strftime('%d'),
            'month': self._get_french_month(start_dt.month),
            'month_short': self._get_french_month_short(start_dt.month),
            'time': time_str,
            'title': event['title'],
            'location': event['location'],
            'description': description_html,
            'event_color': colors[color_index],
            'icon': icon
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
