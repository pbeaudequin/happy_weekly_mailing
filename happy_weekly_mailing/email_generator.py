"""Module pour générer les emails HTML à partir des templates."""

from pathlib import Path
from typing import List, Dict, Any
import re


class EmailGenerator:
    """Génère des emails HTML à partir de templates."""

    def __init__(self, template_name: str = "design_moderne"):
        """
        Initialise le générateur d'emails.

        Args:
            template_name: Nom du template à utiliser (sans extension .html)
                Options: design_moderne, design_classique, design_festif, design_minimaliste
        """
        self.template_name = template_name
        self.template_path = Path(__file__).parent.parent / "templates" / f"{template_name}.html"

        if not self.template_path.exists():
            raise FileNotFoundError(f"Template non trouvé : {self.template_path}")

    def generate(self, events: List[Dict[str, str]]) -> str:
        """
        Génère l'email HTML complet avec les événements.

        Args:
            events: Liste des événements formatés

        Returns:
            HTML complet de l'email
        """
        # Charger le template
        template_html = self.template_path.read_text(encoding='utf-8')

        # Générer le HTML des événements
        events_html = self._generate_events_html(template_html, events)

        # Remplacer la section des événements dans le template
        final_html = self._replace_events_section(template_html, events_html)

        return final_html

    def _generate_events_html(self, template: str, events: List[Dict[str, str]]) -> str:
        """
        Génère le HTML pour tous les événements.

        Args:
            template: Le template HTML complet
            events: Liste des événements formatés

        Returns:
            HTML de tous les événements
        """
        # Extraire le template d'un seul événement
        event_template = self._extract_event_template(template)

        if not event_template:
            return "<p>Erreur : template d'événement non trouvé</p>"

        # Générer le HTML pour chaque événement
        events_html_parts = []
        for event in events:
            event_html = self._fill_event_template(event_template, event)
            events_html_parts.append(event_html)

        return "\n".join(events_html_parts)

    def _extract_event_template(self, template: str) -> str:
        """
        Extrait le template d'un événement unique du template complet.

        Args:
            template: Template HTML complet

        Returns:
            Template HTML d'un seul événement
        """
        # Chercher le contenu entre <!-- EVENT_LOOP_START --> et <!-- EVENT_LOOP_END -->
        pattern = r'<!-- EVENT_LOOP_START -->(.*?)<!-- EVENT_LOOP_END -->'
        match = re.search(pattern, template, re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""

    def _replace_events_section(self, template: str, events_html: str) -> str:
        """
        Remplace la section des événements dans le template.

        Args:
            template: Template HTML complet
            events_html: HTML généré pour tous les événements

        Returns:
            Template avec les événements insérés
        """
        # Remplacer tout le contenu entre les marqueurs
        pattern = r'<!-- EVENT_LOOP_START -->.*?<!-- EVENT_LOOP_END -->'
        result = re.sub(pattern, events_html, template, flags=re.DOTALL)

        return result

    def _fill_event_template(self, event_template: str, event: Dict[str, str]) -> str:
        """
        Remplit le template d'un événement avec ses données.

        Args:
            event_template: Template HTML d'un événement
            event: Données de l'événement

        Returns:
            HTML de l'événement rempli
        """
        result = event_template

        # Remplacer toutes les variables {variable_name}
        for key, value in event.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))

        return result

    @staticmethod
    def get_available_templates() -> List[str]:
        """
        Retourne la liste des templates disponibles.

        Returns:
            Liste des noms de templates (sans extension)
        """
        templates_dir = Path(__file__).parent.parent / "templates"
        if not templates_dir.exists():
            return []

        templates = []
        for file in templates_dir.glob("*.html"):
            templates.append(file.stem)

        return sorted(templates)
