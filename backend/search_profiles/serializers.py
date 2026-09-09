from rest_framework import serializers

from .models import SearchProfile


class SearchProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchProfile
        fields = [
            'id', 'name', 'title_keywords', 'excluded_keywords',
            'yoe_min', 'yoe_max', 'locations', 'remote_ok',
            'salary_floor', 'active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']