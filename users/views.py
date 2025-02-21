from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.contrib.auth import login, logout

from .filters import UserFilter
from .models import User, OwnerProfile
from .serializers import UserSerializer, OwnerProfileSerializer, LoginSerializer
from .permissions import IsUserOrReadOnly, IsOwnerOrAdmin

class UserListView(generics.ListAPIView):
    """
    List all registered users.

    * Requires: Admin authentication
    * Returns: List of user data
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a user’s profile.

    * Requires: Authentication (only owner or admin can modify)
    * Returns: User data or success message on deletion
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsUserOrReadOnly]

class RegisterUserView(APIView):
    """
    Register a new user.

    * Requires: username, email, password, confirm_password
    * Returns: User data and authentication token
    """
    permission_classes = [AllowAny]
    throttle_scope = 'register'  # Scoped to 5/hour

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    Log in an existing user.

    * Requires: username, password
    * Returns: Authentication token and user data
    """
    permission_classes = [AllowAny]
    throttle_scope = 'login'  # Scoped to 10/hour

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """
    Log out an authenticated user.

    * Requires: Authentication token
    * Returns: Success message
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

class OwnerProfileListView(generics.ListCreateAPIView):
    """
    List all owner profiles or create a new one.

    * Requires: Authentication (admin for listing, user for creation)
    * Returns: List of owner profiles or newly created profile data
    """
    queryset = OwnerProfile.objects.all()
    serializer_class = OwnerProfileSerializer
    permission_classes = [IsAuthenticated]

class OwnerProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an owner profile.

    * Requires: Authentication (only owner or admin can modify)
    * Returns: Owner profile data or success message on deletion
    """
    queryset = OwnerProfile.objects.all()
    serializer_class = OwnerProfileSerializer
    permission_classes = [IsOwnerOrAdmin]