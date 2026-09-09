from rest_framework import serializers

from .models import JobSource


class JobSourceSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = JobSource
        fields = [
            'id', 'company_name', 'type', 'type_display', 'config',
            'poll_interval_minutes', 'last_polled_at', 'enabled',
            'is_auto_submit_eligible', 'created_at',
        ]
        read_only_fields = ['id', 'last_polled_at', 'created_at']