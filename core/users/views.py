"""
users/views.py

API Views:
  - RegisterView          POST /api/register/
  - VerifyOTPView         POST /api/verify-otp/
  - VerifiedUsersView     GET  /api/verified-users/
  - CustomTokenObtainPairView  POST /api/login/
  - UserUpdateView        PATCH /api/profile/update/
  - NearbyUsersView       GET  /api/nearby-users/
  - ChatPageView          GET  /chat/  (renders chat.html)
"""

import math
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth import get_user_model

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import OTP, Message
from .serializers import (
    UserRegistrationSerializer,
    OTPVerifySerializer,
    CustomTokenObtainPairSerializer,
    UserUpdateSerializer,
    UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: Haversine distance (km) between two lat/lon points
# ---------------------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula. Returns distance in kilometres.
    """
    R = 6371  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Task 1a: User Registration
# ---------------------------------------------------------------------------
class RegisterView(APIView):
    """
    POST /api/register/
    Public endpoint — no authentication required.
    Creates a new user, generates a 6-digit OTP, and emails it.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        # Generate and persist OTP
        otp_code = OTP.generate_code()
        OTP.objects.create(user=user, code=otp_code)

        # Send OTP via email
        try:
            send_mail(
                subject='Your OTP Verification Code',
                message=(
                    f'Hello {user.name or user.email},\n\n'
                    f'Your OTP code is: {otp_code}\n'
                    f'This code is valid for 5 minutes.\n\n'
                    f'If you did not request this, please ignore this email.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as exc:
            # Log the error but don't block registration
            logger.error("Failed to send OTP email to %s: %s", user.email, exc)

        return Response(
            {
                'message': 'Registration successful. An OTP has been sent to your email.',
                'user_id': user.id,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Task 1b: OTP Verification
# ---------------------------------------------------------------------------
class VerifyOTPView(APIView):
    """
    POST /api/verify-otp/
    Validates the OTP submitted by the user.
    Sets is_verified=True on success.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the most recent OTP for this user
        otp = OTP.objects.filter(user=user, code=code).order_by('-created_at').first()

        if not otp:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response(
                {'error': 'OTP has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark user as verified
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        # Clean up used OTPs
        OTP.objects.filter(user=user).delete()

        return Response({'message': 'Email verified successfully. You can now log in.'})


# ---------------------------------------------------------------------------
# Task 1c: List Verified Users
# ---------------------------------------------------------------------------
class VerifiedUsersView(generics.ListAPIView):
    """
    GET /api/verified-users/
    Returns all users whose is_verified=True.
    Requires authentication.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_verified=True)


# ---------------------------------------------------------------------------
# Task 2: JWT Login
# ---------------------------------------------------------------------------
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/login/
    Uses CustomTokenObtainPairSerializer which blocks unverified users.
    """
    serializer_class = CustomTokenObtainPairSerializer


# ---------------------------------------------------------------------------
# Task 3: Update User Profile
# ---------------------------------------------------------------------------
class UserUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/profile/update/
    Allows the authenticated user to update their own profile.
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch']  # Only PATCH; no full PUT replacement

    def get_object(self):
        # Always operate on the currently authenticated user
        return self.request.user


# ---------------------------------------------------------------------------
# Task 4: Nearby Users (Haversine)
# ---------------------------------------------------------------------------
class NearbyUsersView(APIView):
    """
    GET /api/nearby-users/?radius=5
    Returns verified users within `radius` km (default 5 km) of the
    authenticated user, excluding the user themselves.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        current_user = request.user

        if current_user.latitude is None or current_user.longitude is None:
            return Response(
                {'error': 'Your profile does not have location data. Please update latitude/longitude.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            radius = float(request.query_params.get('radius', 5))
        except ValueError:
            radius = 5.0

        # Fetch all verified users except the current user who have coordinates
        candidates = User.objects.filter(
            is_verified=True,
            latitude__isnull=False,
            longitude__isnull=False,
        ).exclude(pk=current_user.pk)

        nearby = []
        for user in candidates:
            distance = haversine(
                current_user.latitude, current_user.longitude,
                user.latitude, user.longitude,
            )
            if distance <= radius:
                nearby.append(user)

        serializer = UserSerializer(nearby, many=True, context={'request': request})
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Task 5: Chat Page (renders chat.html)
# ---------------------------------------------------------------------------
class ChatPageView(APIView):
    """
    GET /chat/
    Renders the chat HTML page. No authentication enforced at the view
    level so the page itself can load; the WebSocket consumer handles auth.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Pass the last 50 messages for initial render
        messages = Message.objects.select_related('sender').order_by('-timestamp')[:50]
        return render(request, 'chat.html', {'messages': reversed(list(messages))})
