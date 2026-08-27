from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def _tokens_for_user(user):
    """Issue a fresh access/refresh token pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — create an account and return tokens + user."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = _tokens_for_user(user)
        return Response(
            {'user': UserSerializer(user).data, **tokens},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/auth/login/ — authenticate with username-or-email + password."""
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            # Deliberately vague — never reveal whether the username or the
            # password was the one that was wrong.
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = _tokens_for_user(user)
        return Response({'user': UserSerializer(user).data, **tokens})


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the given refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """GET /api/auth/me/ — current user. PATCH to update profile fields."""
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProfileUpdateSerializer
        return UserSerializer


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/ — change the current user's password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)


from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings as django_settings

from .serializers import PasswordResetConfirmSerializer, PasswordResetRequestSerializer


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/ — request a reset link.
    Always returns 200 regardless of whether the email exists, so we never
    leak which emails are registered.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email__iexact=email).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{getattr(django_settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password?uid={uid}&token={token}"
            # In development this goes to the console email backend (see settings).
            send_mail(
                subject='Reset your Movie Playlist Manager password',
                message=f'Use this link to reset your password: {reset_url}',
                from_email=None,
                recipient_list=[user.email],
                fail_silently=True,
            )
        return Response({'detail': 'If that email exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    """POST /api/auth/password-reset/confirm/ — set a new password using uid+token."""
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'detail': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, data['token']):
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data['new_password'])
        user.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)
