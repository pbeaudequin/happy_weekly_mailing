import unittest
from unittest.mock import Mock, patch

import requests

from happy_weekly_mailing.website_recap_fetcher import WebsiteRecapFetcher


class WebsiteRecapFetcherTest(unittest.TestCase):
    def test_parse_phototheque_returns_first_image_per_section(self):
        html = """
        <nav><img src="/logo.png"></nav>
        <h3>Escapade dans l'Est&eacute;ron - 18 juin 2026</h3>
        <a class="jw-album-image" href="/esteron-high.jpg">
            <img class="jw-album-image__image" src="/esteron-thumb.jpg">
        </a>
        <a class="jw-album-image" href="/esteron-2-high.jpg">
            <img class="jw-album-image__image" src="/esteron-2-thumb.jpg">
        </a>
        <h3>Rando aux Balcons du Loup le 14 juin 2026</h3>
        <a class="jw-album-image hidden" href="/hidden-high.jpg">
            <img class="jw-album-image__image" src="/hidden-thumb.jpg">
        </a>
        <a class="jw-album-image" href="/loup-high.jpg">
            <img class="jw-album-image__image" src="/loup-thumb.jpg">
        </a>
        <h3>Rando au bord de la Siagne le 5 juin 2026</h3>
        <a class="jw-album-image" href="/siagne-high.jpg">
            <img class="jw-album-image__image" src="/siagne-thumb.jpg">
        </a>
        """

        items = WebsiteRecapFetcher.parse_phototheque(
            html,
            "https://www.happy-au-rouret.fr/phototheque-2026",
            limit=3,
        )

        self.assertEqual(
            [item.title for item in items],
            [
                "Escapade dans l'Estéron - 18 juin 2026",
                "Rando aux Balcons du Loup le 14 juin 2026",
                "Rando au bord de la Siagne le 5 juin 2026",
            ],
        )
        self.assertEqual(
            items[0].image_url,
            "https://www.happy-au-rouret.fr/esteron-high.jpg",
        )
        self.assertEqual(
            items[0].thumbnail_url,
            "https://www.happy-au-rouret.fr/esteron-thumb.jpg",
        )
        self.assertEqual(
            items[1].thumbnail_url,
            "https://www.happy-au-rouret.fr/loup-thumb.jpg",
        )

    def test_parse_phototheque_returns_empty_list_without_album_items(self):
        items = WebsiteRecapFetcher.parse_phototheque(
            "<h3>Sans album</h3><img src='/navigation.jpg'>",
            "https://www.happy-au-rouret.fr/phototheque-2026",
            limit=3,
        )

        self.assertEqual(items, [])

    @patch("happy_weekly_mailing.website_recap_fetcher.requests.get")
    def test_fetch_latest_surfaces_network_errors_for_caller_fallback(self, get_mock):
        get_mock.side_effect = requests.RequestException("offline")
        fetcher = WebsiteRecapFetcher(year=2026)

        with self.assertRaises(requests.RequestException):
            fetcher.fetch_latest()

    @patch("happy_weekly_mailing.website_recap_fetcher.requests.get")
    def test_fetch_latest_returns_template_contexts(self, get_mock):
        response = Mock()
        response.text = """
        <h3>Rando au bord de la Siagne le 5 juin 2026</h3>
        <a class="jw-album-image" href="/siagne-high.jpg">
            <img class="jw-album-image__image" src="/siagne-thumb.jpg">
        </a>
        """
        response.raise_for_status.return_value = None
        get_mock.return_value = response

        fetcher = WebsiteRecapFetcher(year=2026)
        items = fetcher.fetch_latest(limit=3)

        self.assertEqual(items[0]["recap_title"], "Rando au bord de la Siagne le 5 juin 2026")
        self.assertEqual(
            items[0]["recap_thumbnail_url"],
            "https://www.happy-au-rouret.fr/siagne-thumb.jpg",
        )
        get_mock.assert_called_once_with(
            "https://www.happy-au-rouret.fr/phototheque-2026",
            timeout=10,
        )


if __name__ == "__main__":
    unittest.main()
