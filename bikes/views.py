from rest_framework import generics, permissions
from .models import Bike
from .serializers import BikeSerializer
from .permissions import IsOwnerOrAdmin  # Custom permission

# Anyone can see the list of bikes
class BikeListView(generics.ListAPIView):
    queryset = Bike.objects.filter(is_approved=True, availability_status=True)
    serializer_class = BikeSerializer
    permission_classes = [permissions.AllowAny]  # Public access

# Anyone can view bike details
class BikeDetailView(generics.RetrieveAPIView):
    queryset = Bike.objects.filter(is_approved=True, availability_status=True)
    serializer_class = BikeSerializer
    permission_classes = [permissions.AllowAny]

# Only owners/admins can create bikes
class BikeCreateView(generics.CreateAPIView):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only logged-in users

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)  # Assign owner automatically

# Only owners/admins can update their own bikes
class BikeUpdateView(generics.UpdateAPIView):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IsOwnerOrAdmin]  # Custom permission

# Only owners/admins can delete their own bikes
class BikeDeleteView(generics.DestroyAPIView):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IsOwnerOrAdmin]
