from rest_framework import serializers

from .models import JobPosting


class JobPostingSerializer(serializers.ModelSerializer):
    source_company = serializers.CharField(source='source.company_name', read_only=True)
    source_type = serializers.CharField(source='source.type', read_only=True)

    class Meta:
        model = JobPosting
        fields = [
            'id', 'source', 'source_company', 'source_type',
            'company', 'title', 'location', 'remote', 'url',
            'description_normalized', 'posted_at', 'discovered_at',
            'fit_score', 'fit_rationale', 'missing_skills',
        ]
        read_only_fields = fields  # entire serializer is read-only