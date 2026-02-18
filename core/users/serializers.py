"""
users/serializers.py

Serializers for:
  - UserRegistrationSerializer  — sign-up
  - OTPVerifySerializer         — OTP verification
  - CustomTokenObtainPairSerializer — JWT login (blocks unverified users)
  - UserUpdateSerializer        — profile update
  - UserSerializer              — general read-only representation
"""

import math
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# User Registration
# ---------------------------------------------------------------------------
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles new user sign-up.
    Password is write-only and hashed before saving.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'mobile',
            'profile_image', 'latitude', 'longitude', 'password',
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        # Use create_user so the password is properly hashed
        password = validated_data.pop('password')
        # username defaults to email if not provided
        validated_data.setdefault('username', validated_data['email'])
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ---------------------------------------------------------------------------
# OTP Verification
# ---------------------------------------------------------------------------
class OTPVerifySerializer(serializers.Serializer):
    """Validates the 6-digit OTP submitted by the user."""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


# ---------------------------------------------------------------------------
# Custom JWT Login — blocks unverified users
# ---------------------------------------------------------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends SimpleJWT's default serializer to:
      1. Prevent login if the user has not verified their email (is_verified=False).
      2. Embed extra claims (name, email) into the token payload.
    """

    def validate(self, attrs):
        # Run the standard validation (checks credentials)
        data = super().validate(attrs)

        # Block login for unverified accounts
        if not self.user.is_verified:
            raise serializers.ValidationError(
                "Account not verified. Please verify your email with the OTP sent to you."
            )

        # Add extra user info to the response payload
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
        }
        return data

    @classmethod
    def get_token(cls, user):
        """Embed custom claims inside the JWT payload."""
        token = super().get_token(user)
        token['email'] = user.email
        token['name'] = user.name
        return token


# ---------------------------------------------------------------------------
# User Update
# ---------------------------------------------------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    """Allows an authenticated user to update their own profile fields."""

    class Meta:
        model = User
        fields = ['name', 'mobile', 'profile_image', 'latitude', 'longitude']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ---------------------------------------------------------------------------
# General User Read Serializer
# ---------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer used for listing users and nearby-user results."""

    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'mobile',
            'profile_image', 'latitude', 'longitude', 'is_verified',
        ]
