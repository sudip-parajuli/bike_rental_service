from django.shortcuts import render, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .forms import BikeOwnerCreateForm
from .models import Bike
from .serializers import BikeSerializer, BikeOwnerCreateSerializer
from .permissions import IsOwnerOrAdmin
from .filters import BikeFilter
from django.contrib import messages

class CustomPagination(PageNumberPagination):
    page_size = 6  # Default page size
    page_size_query_param = 'page_size'  # Allow overriding via query parameter
    max_page_size = 100  # Maximum allowed page size

class BikeListView(generics.ListAPIView):
    """
    List all approved and available bikes, optionally filtered by is_featured, availability, type, or search.

    * Requires: None (public access)
    * Returns: List of bike data (JSON for API, template for non-API)
    """
    serializer_class = BikeSerializer
    permission_classes = [permissions.AllowAny]  # Public access
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = BikeFilter
    search_fields = ['name', 'model_year', 'type', 'description']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = Bike.objects.filter(is_approved=True).order_by('name')
        return queryset

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            # Return JSON for API requests (e.g., /api/bike/)
            return super().get(request, *args, **kwargs)
        # Render template for non-API requests (e.g., /bike/)
        bikes = self.filter_queryset(self.get_queryset())
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(bikes, request)
        return render(request, 'bikes/bike_list.html', {'bikes': page})

class BikeDetailView(generics.RetrieveAPIView):
    """
    Display details of a specific bike.

    * Requires: None (public access)
    * Returns: JSON bike data for API, renders template for non-API
    """
    serializer_class = BikeSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Bike.objects.filter(is_approved=True)

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            # Return JSON for API requests (e.g., /api/bike/<pk>/)
            return super().get(request, *args, **kwargs)
        # Render template for non-API requests (e.g., /bike/<pk>/)
        bike = self.get_object()
        return render(request, 'bikes/bike_detail.html', {'bike': bike})

class BikeCreateView(generics.CreateAPIView):
    """
    Create a new bike listing for owners, with admin approval required.

    * Requires: Authentication
    * Returns: Newly created bike data or renders a form for non-API requests
    """
    queryset = Bike.objects.all()
    serializer_class = BikeOwnerCreateSerializer  # For API requests
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, availability_status=False, is_approved=False, is_featured=False)

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return super().post(request, *args, **kwargs)
        form = BikeOwnerCreateForm(request.POST, request.FILES)
        if form.is_valid():
            bike = form.save(commit=False)
            bike.owner = request.user
            bike.availability_status = False
            bike.is_approved = False
            bike.is_featured = False
            bike.save()
            messages.success(request, "Your bike listing has been submitted. An admin will review it soon.")
            return redirect('users:bike-owner-dashboard')
        return render(request, 'bikes/bike_create_owner.html', {'form': form})

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        form = BikeOwnerCreateForm()
        return render(request, 'bikes/bike_create_owner.html', {'form': form})

class BikeUpdateView(generics.UpdateAPIView):
    """
    Update an existing bike listing.

    * Requires: Authentication (only owner or admin)
    * Returns: Updated bike data
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        # Use BikeOwnerCreateSerializer for owners, BikeSerializer for admins
        if self.request.user == self.get_object().owner and not self.request.user.is_superuser:
            return BikeOwnerCreateSerializer
        return BikeSerializer

class BikeDeleteView(generics.DestroyAPIView):
    """
    Delete a bike listing.

    * Requires: Authentication (only owner or admin)
    * Returns: Success message
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IsOwnerOrAdmin]