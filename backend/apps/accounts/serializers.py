from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.credits.services import ensure_wallet, grant_points
from apps.subscriptions.services import assign_free_subscription

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "auth_provider",
            "google_sub",
            "is_active",
            "is_staff",
            "created_at",
            "updated_at",
            "referral_code",
        ]
        read_only_fields = fields


class AuthConfigSerializer(serializers.Serializer):
    google_only = serializers.BooleanField()
    local_auth_enabled = serializers.BooleanField()
    registration_enabled = serializers.BooleanField()
    supported_languages = serializers.ListField(child=serializers.CharField())
    default_language = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    name = serializers.CharField(max_length=255)
    referral_code = serializers.CharField(max_length=12, required=False, allow_blank=True)

    def validate(self, attrs):
        if self.context["request"].app_settings.GOOGLE_ONLY:
            raise serializers.ValidationError("Local registration is disabled when GOOGLE_ONLY=true.")
        return attrs

    def create(self, validated_data):
        referral_code = validated_data.pop("referral_code", "")
        user = User.objects.create_user(
            auth_provider=User.AuthProvider.LOCAL,
            is_email_verified=True,
            **validated_data,
        )
        ensure_wallet(user)
        assign_free_subscription(user)
        grant_points(user, 10, "registration_bonus", "Registration bonus")
        if referral_code:
            from apps.referrals.services import register_referral

            register_referral(referred_user=user, referral_code=referral_code)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context["request"]
        if request.app_settings.GOOGLE_ONLY:
            raise serializers.ValidationError("Local login is disabled when GOOGLE_ONLY=true.")
        user = authenticate(request=request, email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive.")
        attrs["user"] = user
        return attrs


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField()


class RefreshSerializer(TokenObtainPairSerializer):
    pass
