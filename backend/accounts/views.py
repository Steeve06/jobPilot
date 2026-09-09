from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import CurrentUserSerializer


class CsrfCookieView(APIView):
    """
    GET this once when the React app boots, before attempting login.
    It doesn't return meaningful data — its only job is to make Django
    set the csrftoken cookie in the browser, which the frontend then
    reads and echoes back as an X-CSRFToken header on POST requests.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)  # forces the cookie to be set
        return Response({'detail': 'CSRF cookie set'})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'Invalid credentials'}, status=400)
        login(request, user)
        return Response({'detail': 'Logged in'})


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'Logged out'})


class CurrentUserView(APIView):
    def get(self, request):
        profiles = Profile.objects.filter(user=request.user)
        data = CurrentUserSerializer({
            'username': request.user.username,
            'profiles': profiles,
        }).data
        return Response(data)