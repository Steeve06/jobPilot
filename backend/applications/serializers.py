from rest_framework import serializers

from .models import Application, Note, StatusEvent


class StatusEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusEvent
        fields = ['id', 'status', 'source', 'confirmed', 'occurred_at']
        read_only_fields = ['id', 'occurred_at']


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    status_events = StatusEventSerializer(many=True, read_only=True)
    notes = NoteSerializer(many=True, read_only=True)
    posting_title = serializers.CharField(source='posting.title', read_only=True)
    posting_company = serializers.CharField(source='posting.company', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'posting', 'posting_title', 'posting_company',
            'tailored_resume', 'status', 'applied_at', 'submission_method',
            'next_action_date', 'contact_email', 'status_events', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_posting(self, posting):
        if self.instance is not None:
            return posting
        request = self.context['request']
        from accounts.services import get_active_profile
        active_profile = get_active_profile(request)
        if posting.source.profile_id != active_profile.id:
            raise serializers.ValidationError('This posting does not belong to your active profile.')
        return posting

    def update(self, instance, validated_data):
        validated_data.pop('posting', None)
        new_status = validated_data.get('status')
        status_changed = new_status is not None and new_status != instance.status

        instance = super().update(instance, validated_data)

        if status_changed:
            StatusEvent.objects.create(
                application=instance,
                status=new_status,
                source=StatusEvent.Source.MANUAL,
                confirmed=True,
            )
        return instance