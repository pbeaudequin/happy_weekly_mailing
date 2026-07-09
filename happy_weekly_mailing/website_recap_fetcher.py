"""Module pour recuperer les derniers contenus du site Happy au Rouret."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List
from urllib.parse import urldefrag, urljoin

import pytz
import requests


@dataclass
class WebsiteRecapItem:
    """Contenu recent a afficher dans l'email recapitulatif."""

    title: str
    url: str
    image_url: str
    thumbnail_url: str

    def as_template_context(self) -> Dict[str, str]:
        """Retourne les champs attendus par les templates HTML."""
        return {
            "recap_title": self.title,
            "recap_url": self.url,
            "recap_image_url": self.image_url,
            "recap_thumbnail_url": self.thumbnail_url,
        }


class _PhotothequeParser(HTMLParser):
    """Extrait le premier visuel de chaque section Webador de phototheque."""

    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.items: List[WebsiteRecapItem] = []
        self._current_title = ""
        self._seen_titles: set[str] = set()
        self._heading_tag = ""
        self._heading_parts: List[str] = []
        self._heading_anchor = ""
        self._current_title_anchor = ""
        self._current_album_anchor = ""
        self._webador_element_stack: List[str] = []
        self._pending_album_link: Dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]) -> None:
        attrs_dict = {name: value or "" for name, value in attrs}
        class_names = attrs_dict.get("class", "")

        if tag == "div":
            self._webador_element_stack.append(self._get_webador_element_id(attrs_dict))

        if tag in {"h1", "h2", "h3"}:
            self._heading_tag = tag
            self._heading_parts = []
            self._heading_anchor = self._nearest_webador_element_id()
            return

        if (
            tag == "div"
            and self._current_title
            and self._current_title not in self._seen_titles
            and "jw-album-raster" in class_names
        ):
            self._current_album_anchor = attrs_dict.get("id", "")
            return

        if tag == "a" and "jw-album-image" in class_names and "hidden" not in class_names:
            href = attrs_dict.get("href")
            if self._current_title and href and self._current_title not in self._seen_titles:
                self._pending_album_link = {
                    "href": href,
                    "image_url": "",
                    "anchor": self._current_title_anchor
                    or self._current_album_anchor
                    or attrs_dict.get("id", ""),
                }
            return

        if tag == "img" and self._pending_album_link is not None:
            self._pending_album_link["image_url"] = attrs_dict.get("src", "")
            self._commit_pending_album_link()

    def handle_endtag(self, tag: str) -> None:
        if tag == self._heading_tag:
            title = " ".join("".join(self._heading_parts).split())
            if title:
                self._current_title = unescape(title)
                self._current_title_anchor = self._heading_anchor
                self._current_album_anchor = ""
            self._heading_tag = ""
            self._heading_parts = []
            self._heading_anchor = ""
            return

        if tag == "a" and self._pending_album_link is not None:
            self._commit_pending_album_link()

        if tag == "div" and self._webador_element_stack:
            self._webador_element_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._heading_tag:
            self._heading_parts.append(data)

    @staticmethod
    def _get_webador_element_id(attrs: Dict[str, str]) -> str:
        element_id = attrs.get("id", "")
        if element_id.startswith("jw-element-"):
            return element_id
        return ""

    def _nearest_webador_element_id(self) -> str:
        for element_id in reversed(self._webador_element_stack):
            if element_id:
                return element_id
        return ""

    def _anchored_page_url(self, anchor: str) -> str:
        page_url, _fragment = urldefrag(self.page_url)
        if not anchor:
            return page_url
        return f"{page_url}#{anchor}"

    def _commit_pending_album_link(self) -> None:
        if self._pending_album_link is None or not self._current_title:
            self._pending_album_link = None
            return

        href = self._pending_album_link["href"]
        image_url = self._pending_album_link["image_url"] or href
        anchor = self._pending_album_link["anchor"]
        self.items.append(
            WebsiteRecapItem(
                title=self._current_title,
                url=self._anchored_page_url(anchor),
                image_url=urljoin(self.page_url, href),
                thumbnail_url=urljoin(self.page_url, image_url),
            )
        )
        self._seen_titles.add(self._current_title)
        self._pending_album_link = None


class WebsiteRecapFetcher:
    """Recupere les derniers articles/photos de la phototheque Happy au Rouret."""

    def __init__(
        self,
        base_url: str = "https://www.happy-au-rouret.fr",
        timezone: str = "Europe/Paris",
        year: int | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timezone = pytz.timezone(timezone)
        self.year = year

    def fetch_latest(self, limit: int = 3) -> List[Dict[str, str]]:
        """
        Recupere les derniers contenus du site.

        Args:
            limit: Nombre maximum de contenus a retourner

        Returns:
            Liste de dictionnaires prets pour les templates email
        """
        page_url = self._get_phototheque_url()
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()

        items = self.parse_phototheque(response.text, page_url, limit)
        return [item.as_template_context() for item in items]

    def _get_phototheque_url(self) -> str:
        year = self.year or datetime.now(self.timezone).year
        return f"{self.base_url}/phototheque-{year}"

    @staticmethod
    def parse_phototheque(
        html_content: str,
        page_url: str,
        limit: int = 3,
    ) -> List[WebsiteRecapItem]:
        """
        Parse une page Webador de phototheque.

        La page liste les contenus du plus recent au plus ancien. On garde le
        premier visuel de chaque section titree pour eviter de transformer les
        albums entiers en doublons.
        """
        parser = _PhotothequeParser(page_url)
        parser.feed(html_content)
        return parser.items[:limit]
