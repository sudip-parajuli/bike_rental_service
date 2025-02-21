from rest_framework import generics, permissions
from .models import Bike
from .serializers import BikeSerializer
from .permissions import IsOwnerOrAdmin  # Custom permission
from .filters import BikeFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

# Anyone can see the list of bikes
class BikeListView(generics.ListAPIView):
    """
        List all approved and available bikes.

        * Requires: None (public access)
        * Returns: List of bike data
    """
    queryset = Bike.objects.filter(is_approved=True, availability_status=True)
    serializer_class = BikeSerializer
    permission_classes = [permissions.AllowAny]  # Public access
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = BikeFilter
    search_fields = ['name', 'model_year', 'type', 'brand',]

# Anyone can view bike details
class BikeDetailView(generics.RetrieveAPIView):
    """
        Retrieve details of a specific bike.

        * Requires: None (public access)
        * Returns: Bike data
    """
    queryset = Bike.objects.filter(is_approved=True, availability_status=True)
    serializer_class = BikeSerializer
    permission_classes = [permissions.AllowAny]

# Only owners/admins can create bikes
class BikeCreateView(generics.CreateAPIView):
    """
        Create a new bike listing.

        * Requires: Authentication
        * Returns: Newly created bike data
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only logged-in users

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)  # Assign owner automatically

# Only owners/admins can update their own bikes
class BikeUpdateView(generics.UpdateAPIView):
    """
        Update an existing bike listing.

        * Requires: Authentication (only owner or admin)
        * Returns: Updated bike data
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IsOwnerOrAdmin]  # Custom permission

# Only owners/admins can delete their own bikes
class BikeDeleteView(generics.DestroyAPIView):
    """
        Delete a bike listing.

        * Requires: Authentication (only owner or admin)
        * Returns: Success message
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IsOwnerOrAdmin]
