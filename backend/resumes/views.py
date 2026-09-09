from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.services import get_active_profile
from .models import Resume
from .serializers import ResumeSerializer


class ResumeDetailView(APIView):
    def get_object(self, request):
        profile = get_active_profile(request)
        resume, _ = Resume.objects.get_or_create(
            profile=profile,
            defaults={'full_name': '', 'email': ''},
        )
        return resume

    def get(self, request):
        resume = self.get_object(request)
        return Response(ResumeSerializer(resume).data)

    def patch(self, request):
        resume = self.get_object(request)
        serializer = ResumeSerializer(resume, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)