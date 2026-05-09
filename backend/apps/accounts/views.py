from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as django_logout
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import (
    AuthConfigSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.accounts.services import (
    get_auth_config,
    touch_daily_login_reward,
    upsert_google_user,
    verify_google_credential,
)


class AppSettingsMixin:
    def initial(self, request, *args, **kwargs):
        request.app_settings = settings
        return super().initial(request, *args, **kwargs)


def _build_auth_response(user, request, grant_daily_reward: bool = True):
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    if grant_daily_reward:
        touch_daily_login_reward(
            user,
            ip_address=_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )
    response = Response(
        {
            "user": UserSerializer(user).data,
            "access": access,
            "refresh_expires_in_days": settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].days,
        }
    )
    response.set_cookie(
        "refresh_token",
        str(refresh),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
    )
    return response


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuthConfigView(AppSettingsMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(AuthConfigSerializer(get_auth_config()).data)


class RegisterView(AppSettingsMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _build_auth_response(user, request, grant_daily_reward=False)


class LoginView(AppSettingsMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return _build_auth_response(serializer.validated_data["user"], request)


class GoogleLoginView(AppSettingsMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_data = verify_google_credential(serializer.validated_data["credential"])
        user = upsert_google_user(token_data)
        return _build_auth_response(user, request)


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()
        except TokenError:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        User = get_user_model()
        user = User.objects.get(id=refresh["user_id"])
        new_refresh = RefreshToken.for_user(user)
        response = Response({"access": str(new_refresh.access_token)})
        response.set_cookie(
            "refresh_token",
            str(new_refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        )
        return response


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("refresh_token")
        django_logout(request)
        return response


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
