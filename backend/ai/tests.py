from django.test import TestCase
from django.contrib.auth.models import User
from .service import _extract_json_block
from accounts.models import Profile
from resumes.models import Bullet, Experience, Resume
from .service import _build_tailored_content


class ExtractJsonBlockTests(TestCase):
    def test_bare_json_passes_through_unchanged(self):
        text = '{"full_name": "Alex"}'
        self.assertEqual(_extract_json_block(text), text)

    def test_strips_json_markdown_fence(self):
        text = '```json\n{"full_name": "Alex"}\n```'
        self.assertEqual(_extract_json_block(text), '{"full_name": "Alex"}')

    def test_strips_bare_markdown_fence_no_language_tag(self):
        text = '```\n{"full_name": "Alex"}\n```'
        self.assertEqual(_extract_json_block(text), '{"full_name": "Alex"}')

    def test_strips_preamble_text_before_json(self):
        text = 'Here is the extracted resume data:\n{"full_name": "Alex"}'
        self.assertEqual(_extract_json_block(text), '{"full_name": "Alex"}')

    def test_handles_nested_braces_correctly(self):
        text = '```json\n{"full_name": "Alex", "experiences": [{"company": "Acme"}]}\n```'
        result = _extract_json_block(text)
        self.assertTrue(result.startswith('{'))
        self.assertTrue(result.endswith('}'))
        self.assertIn('"company": "Acme"', result)
        