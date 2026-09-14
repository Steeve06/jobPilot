from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'is_default', 'onboarded']


class CurrentUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    profiles = ProfileSerializer(many=True)