"""
users/urls.py

URL patterns for the users app.
All API endpoints are prefixed with /api/ (set in core/urls.py).
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    VerifyOTPView,
    VerifiedUsersView,
    CustomTokenObtainPairView,
    UserUpdateView,
    NearbyUsersView,
    ChatPageView,
)

urlpatterns = [
    # ── Task 1: Registration & OTP ──────────────────────────────────────────
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('verified-users/', VerifiedUsersView.as_view(), name='verified-users'),

    # ── Task 2: JWT Auth ────────────────────────────────────────────────────
    path('login/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # ── Task 3: Profile Update ──────────────────────────────────────────────
    path('profile/update/', UserUpdateView.as_view(), name='profile-update'),

    # ── Task 4: Nearby Users ────────────────────────────────────────────────
    path('nearby-users/', NearbyUsersView.as_view(), name='nearby-users'),

    # ── Task 5: Chat Page ───────────────────────────────────────────────────
    path('chat/', ChatPageView.as_view(), name='chat'),
]
