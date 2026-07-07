"""Module pour générer les emails HTML à partir des templates."""

from pathlib import Path
from html import escape
from typing import List, Dict
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

    def generate(
        self,
        events: List[Dict[str, str]],
        recap_items: List[Dict[str, str]] | None = None,
    ) -> str:
        """
        Génère l'email HTML complet avec les événements.

        Args:
            events: Liste des événements formatés
            recap_items: Derniers contenus du site a afficher en introduction

        Returns:
            HTML complet de l'email
        """
        # Charger le template
        template_html = self.template_path.read_text(encoding='utf-8')

        # Générer le HTML des événements
        events_html = self._generate_events_html(template_html, events)
        recap_html = self._generate_recap_html(template_html, recap_items or [])

        # Remplacer les sections dynamiques dans le template
        final_html = self._replace_events_section(template_html, events_html)
        final_html = self._replace_recap_section(final_html, recap_html)

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

        # Joindre avec un saut de ligne
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
        pattern = r'<!-- EVENT_LOOP_START -->\n?(.*?)\n?<!-- EVENT_LOOP_END -->'
        match = re.search(pattern, template, re.DOTALL)

        if match:
            # Ne pas strip complètement pour préserver l'indentation relative
            content = match.group(1)
            # Supprimer seulement les lignes vides au début et à la fin
            lines = content.split('\n')
            # Trouver la première et dernière ligne non vide
            start_idx = 0
            end_idx = len(lines) - 1
            while start_idx < len(lines) and not lines[start_idx].strip():
                start_idx += 1
            while end_idx >= 0 and not lines[end_idx].strip():
                end_idx -= 1
            if start_idx <= end_idx:
                return '\n'.join(lines[start_idx:end_idx + 1])
            return ""

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

    def _generate_recap_html(
        self,
        template: str,
        recap_items: List[Dict[str, str]],
    ) -> str:
        """
        Génère le HTML pour les contenus récents du site.

        Args:
            template: Le template HTML complet
            recap_items: Liste des contenus récents formatés

        Returns:
            HTML de tous les contenus récents, ou chaîne vide si aucun contenu
        """
        if not recap_items:
            return ""

        recap_template = self._extract_recap_template(template)
        if not recap_template:
            return ""

        recap_html_parts = []
        for item in recap_items:
            recap_html_parts.append(self._fill_recap_template(recap_template, item))

        return "\n".join(recap_html_parts)

    def _extract_recap_template(self, template: str) -> str:
        """Extrait le template d'un item recap."""
        pattern = r'<!-- RECAP_LOOP_START -->\n?(.*?)\n?<!-- RECAP_LOOP_END -->'
        match = re.search(pattern, template, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _replace_recap_section(self, template: str, recap_html: str) -> str:
        """
        Remplace ou supprime la section recap selon les contenus disponibles.

        La section complete est optionnelle pour conserver la compatibilite des
        anciens templates et eviter un bloc vide dans l'email.
        """
        section_pattern = r'\n?\s*<!-- RECAP_SECTION_START -->.*?<!-- RECAP_SECTION_END -->'
        if not re.search(section_pattern, template, re.DOTALL):
            return template

        if not recap_html:
            return re.sub(section_pattern, "", template, flags=re.DOTALL)

        loop_pattern = r'<!-- RECAP_LOOP_START -->.*?<!-- RECAP_LOOP_END -->'
        result = re.sub(loop_pattern, recap_html, template, flags=re.DOTALL)
        result = result.replace("<!-- RECAP_SECTION_START -->", "")
        result = result.replace("<!-- RECAP_SECTION_END -->", "")
        return result

    def _fill_recap_template(
        self,
        recap_template: str,
        recap_item: Dict[str, str],
    ) -> str:
        """
        Remplit le template d'un contenu recent avec ses donnees echappees.
        """
        result = recap_template
        for key, value in recap_item.items():
            escaped_value = escape(str(value), quote=True)
            result = result.replace(f"{{{key}}}", escaped_value)
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
