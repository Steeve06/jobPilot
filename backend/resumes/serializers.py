from django.core.validators import URLValidator
from rest_framework import serializers

from .models import Bullet, Experience, Project, Resume


class BulletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bullet
        fields = ['id', 'text', 'skill_tags', 'order']


class ExperienceSerializer(serializers.ModelSerializer):
    bullets = BulletSerializer(many=True)

    class Meta:
        model = Experience
        fields = ['id', 'company', 'title', 'start_date', 'end_date', 'order', 'bullets']


class ProjectSerializer(serializers.ModelSerializer):
    bullets = BulletSerializer(many=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'order', 'bullets']


class ResumeSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True)
    projects = ProjectSerializer(many=True)

    # Declared explicitly as CharField (not the auto-generated URLField)
    # so we can normalize a bare domain into a full URL *before* format
    # validation runs, rather than after — ModelSerializer's default
    # URLField validates format in to_internal_value(), which happens
    # before validate_<field>() is ever called, too late to fix it there.
    linkedin_url = serializers.CharField(required=False, allow_blank=True)
    github_url = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Resume
        fields = [
            'id', 'full_name', 'email', 'phone', 'location',
            'linkedin_url', 'github_url', 'summary', 'skills',
            'education', 'experiences', 'projects', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']

    def validate_linkedin_url(self, value):
        return self._normalize_and_validate_url(value)

    def validate_github_url(self, value):
        return self._normalize_and_validate_url(value)

    def _normalize_and_validate_url(self, value):
        if not value:
            return value
        if not value.startswith(('http://', 'https://')):
            value = f'https://{value}'
        URLValidator()(value)  # raises DRF-compatible ValidationError if still malformed
        return value

    def update(self, instance, validated_data):
        experiences_data = validated_data.pop('experiences', None)
        projects_data = validated_data.pop('projects', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if experiences_data is not None:
            self._sync_children(instance, 'experiences', Experience, experiences_data)
        if projects_data is not None:
            self._sync_children(instance, 'projects', Project, projects_data)

        return instance

    def _sync_children(self, resume, related_name, model_cls, items_data):
        manager = getattr(resume, related_name)
        existing_ids = set(manager.values_list('id', flat=True))
        sent_ids = {item['id'] for item in items_data if 'id' in item}

        manager.filter(id__in=existing_ids - sent_ids).delete()

        for item_data in items_data:
            bullets_data = item_data.pop('bullets', [])
            item_id = item_data.pop('id', None)

            if item_id and item_id in existing_ids:
                child = manager.get(id=item_id)
                for attr, value in item_data.items():
                    setattr(child, attr, value)
                child.save()
            else:
                child = manager.create(**item_data)

            self._sync_bullets(child, bullets_data)

    def _sync_bullets(self, parent, bullets_data):
        existing_ids = set(parent.bullets.values_list('id', flat=True))
        sent_ids = {b['id'] for b in bullets_data if 'id' in b}
        parent.bullets.filter(id__in=existing_ids - sent_ids).delete()

        fk_field = 'experience' if isinstance(parent, Experience) else 'project'

        for bullet_data in bullets_data:
            bullet_id = bullet_data.pop('id', None)
            if bullet_id and bullet_id in existing_ids:
                bullet = Bullet.objects.get(id=bullet_id)
                for attr, value in bullet_data.items():
                    setattr(bullet, attr, value)
                bullet.save()
            else:
                Bullet.objects.create(**{fk_field: parent}, **bullet_data)