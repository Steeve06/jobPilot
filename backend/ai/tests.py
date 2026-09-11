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
        
class BuildTailoredContentTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.resume = Resume.objects.create(
            profile=profile, full_name='Alex Johnson', email='a@x.com', skills=['Go'],
        )
        self.exp = Experience.objects.create(
            resume=self.resume, company='Acme', title='SWE', start_date='2021-01-01',
        )
        self.b1 = Bullet.objects.create(experience=self.exp, text='Did thing A', skill_tags=['Go'])
        self.b2 = Bullet.objects.create(experience=self.exp, text='Did thing B', skill_tags=['AWS'])
        self.b3 = Bullet.objects.create(experience=self.exp, text='Did thing C', skill_tags=[])

    def test_valid_bullet_ids_are_selected_and_ordered(self):
        parsed = {
            'summary': 'A great engineer.',
            'experience_bullet_order': {str(self.exp.id): [self.b2.id, self.b1.id]},
        }
        content = _build_tailored_content(self.resume, parsed)
        bullets = content['experiences'][0]['bullets']
        self.assertEqual([b['text'] for b in bullets], ['Did thing B', 'Did thing A'])

    def test_hallucinated_bullet_id_is_silently_ignored(self):
        fake_id = 999999
        parsed = {
            'summary': 'A great engineer.',
            'experience_bullet_order': {str(self.exp.id): [self.b1.id, fake_id]},
        }
        content = _build_tailored_content(self.resume, parsed)
        bullets = content['experiences'][0]['bullets']
        # Only the real bullet should appear — the fake id is dropped, not inserted as content
        self.assertEqual(len(bullets), 1)
        self.assertEqual(bullets[0]['text'], 'Did thing A')

    def test_bullet_text_always_comes_from_database_not_model_output(self):
        # Even if the model's JSON somehow included a 'text' key alongside an id,
        # _build_tailored_content never reads bullet text from parsed input —
        # only from the Bullet objects themselves.
        parsed = {
            'summary': 'A great engineer.',
            'experience_bullet_order': {
                str(self.exp.id): [self.b1.id],
            },
        }
        content = _build_tailored_content(self.resume, parsed)
        self.assertEqual(content['experiences'][0]['bullets'][0]['text'], 'Did thing A')
        # Confirm skill_tags also comes from the DB record, not the model
        self.assertEqual(content['experiences'][0]['bullets'][0]['skill_tags'], ['Go'])

    def test_empty_or_all_invalid_ids_falls_back_to_all_bullets(self):
        parsed = {
            'summary': 'A great engineer.',
            'experience_bullet_order': {str(self.exp.id): [999999]},  # only a fake id
        }
        content = _build_tailored_content(self.resume, parsed)
        bullets = content['experiences'][0]['bullets']
        self.assertEqual(len(bullets), 3)  # fell back to all 3 real bullets

    def test_summary_falls_back_to_original_if_model_omits_it(self):
        self.resume.summary = 'Original summary.'
        self.resume.save()
        parsed = {'experience_bullet_order': {}}
        content = _build_tailored_content(self.resume, parsed)
        self.assertEqual(content['summary'], 'Original summary.')