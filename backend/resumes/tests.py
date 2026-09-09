from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Profile
from .models import Bullet, Experience, Resume


class BulletConstraintTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.resume = Resume.objects.create(profile=profile, full_name='Alex Johnson', email='a@x.com')
        self.experience = Experience.objects.create(
            resume=self.resume, company='Acme', title='SWE',
            start_date='2021-01-01',
        )

    def test_bullet_with_only_experience_is_valid(self):
        bullet = Bullet(experience=self.experience, text='Did a thing', skill_tags=['Go'])
        bullet.full_clean()  # should not raise
        bullet.save()
        self.assertEqual(Bullet.objects.count(), 1)

    def test_bullet_with_no_parent_fails_validation(self):
        bullet = Bullet(text='Orphan bullet')
        with self.assertRaises(ValidationError):
            bullet.full_clean()

    def test_bullet_with_both_parents_violates_db_constraint(self):
        from .models import Project
        project = Project.objects.create(resume=self.resume, name='Side Project')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Bullet.objects.create(
                    experience=self.experience, project=project, text='Bad bullet',
                )


class ResumeProfileRelationTests(TestCase):
    def test_resume_is_one_per_profile(self):
        user = User.objects.create_user(username='sam', password='pw')
        profile = Profile.objects.create(user=user, name='Data Track')
        Resume.objects.create(profile=profile, full_name='Sam', email='s@x.com')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Resume.objects.create(profile=profile, full_name='Sam Again', email='s2@x.com')