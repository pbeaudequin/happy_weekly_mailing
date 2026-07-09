import unittest

from happy_weekly_mailing.email_generator import EmailGenerator


class EmailGeneratorRecapTest(unittest.TestCase):
    def test_generate_removes_recap_section_when_no_recap_items(self):
        html = EmailGenerator("design_classique").generate(events=[], recap_items=[])

        self.assertNotIn("RECAP_SECTION_START", html)
        self.assertNotIn("RECAP_LOOP_START", html)
        self.assertNotIn("Dernières nouvelles en images", html)

    def test_generate_inserts_escaped_recap_items(self):
        html = EmailGenerator("design_classique").generate(
            events=[],
            recap_items=[
                {
                    "recap_title": "Rando & partage <script>",
                    "recap_url": "https://example.test/photos?x=1&y=2#jw-element-123",
                    "recap_image_url": "https://example.test/full.jpg",
                    "recap_thumbnail_url": "https://example.test/thumb.jpg",
                }
            ],
        )

        self.assertNotIn("RECAP_SECTION_START", html)
        self.assertNotIn("RECAP_LOOP_START", html)
        self.assertIn("Dernières nouvelles en images", html)
        self.assertIn("Rando &amp; partage &lt;script&gt;", html)
        self.assertIn("https://example.test/photos?x=1&amp;y=2#jw-element-123", html)
        self.assertIn("https://example.test/thumb.jpg", html)


if __name__ == "__main__":
    unittest.main()
