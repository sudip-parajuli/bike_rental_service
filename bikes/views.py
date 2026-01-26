from django.shortcuts import render, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .forms import BikehostCreateForm
from .models import Bike
from .serializers import BikeSerializer, BikehostCreateSerializer, BikeRecommendationSerializer
from .permissions import IshostOrAdmin
from .filters import BikeFilter
from .recommendations import get_recommendations_for_user, get_popular_bikes, get_similar_bikes
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
    Create a new bike listing for hosts, with admin approval required.

    * Requires: Authentication
    * Returns: Newly created bike data or renders a form for non-API requests
    """
    queryset = Bike.objects.all()
    serializer_class = BikehostCreateSerializer  # For API requests
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user, availability_status=False, is_approved=False, is_featured=False)

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return super().post(request, *args, **kwargs)
        form = BikehostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            bike = form.save(commit=False)
            bike.host = request.user
            bike.availability_status = False
            bike.is_approved = False
            bike.is_featured = False
            bike.save()
            messages.success(request, "Your bike listing has been submitted. An admin will review it soon.")
            return redirect('users:bike-host-dashboard')
        return render(request, 'bikes/bike_create_host.html', {'form': form})

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        form = BikehostCreateForm()
        return render(request, 'bikes/bike_create_host.html', {'form': form})

class BikeUpdateView(generics.UpdateAPIView):
    """
    Update an existing bike listing.

    * Requires: Authentication (only host or admin)
    * Returns: Updated bike data or renders a form for non-API requests
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IshostOrAdmin]

    def get_serializer_class(self):
        # Use BikehostCreateSerializer for hosts, BikeSerializer for admins
        if self.request.user == self.get_object().host and not self.request.user.is_superuser:
            return BikehostCreateSerializer
        return BikeSerializer

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        bike = self.get_object()
        form = BikehostCreateForm(instance=bike)
        return render(request, 'bikes/bike_update_host.html', {'form': form, 'bike': bike})

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return super().put(request, *args, **kwargs)
        bike = self.get_object()
        form = BikehostCreateForm(request.POST, request.FILES, instance=bike)
        if form.is_valid():
            form.save()
            messages.success(request, "Your bike listing has been updated successfully.")
            return redirect('users:bike-host-dashboard')
        return render(request, 'bikes/bike_update_host.html', {'form': form, 'bike': bike})

class BikeDeleteView(generics.DestroyAPIView):
    """
    Delete a bike listing.

    * Requires: Authentication (only host or admin)
    * Returns: Success message or renders confirmation page for non-API requests
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IshostOrAdmin]

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        bike = self.get_object()
        return render(request, 'bikes/bike_delete_confirm.html', {'bike': bike})

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return super().delete(request, *args, **kwargs)
        bike = self.get_object()
        bike_name = bike.name
        bike.delete()
        messages.success(request, f"Bike listing '{bike_name}' has been deleted successfully.")
        return redirect('users:bike-host-dashboard')


class BikeRecommendationsView(generics.ListAPIView):
    """
    Get personalized bike recommendations for the authenticated user.
    
    Query Parameters:
    - strategy: 'popularity', 'content', 'collaborative', or 'hybrid' (default: 'hybrid')
    - limit: Number of recommendations (default: 6)
    
    * Requires: None (works for both authenticated and anonymous users)
    * Returns: List of recommended bikes with scores and reasons
    """
    serializer_class = BikeRecommendationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable pagination for recommendations
    
    def get_queryset(self):
        user = self.request.user if self.request.user.is_authenticated else None
        strategy = self.request.query_params.get('strategy', 'hybrid')
        limit = int(self.request.query_params.get('limit', 6))
        
        if user:
            recommendations = get_recommendations_for_user(user, strategy=strategy, limit=limit)
        else:
            # For anonymous users, show popular bikes
            recommendations = get_popular_bikes(limit=limit)
        
        return recommendations


class SimilarBikesView(generics.ListAPIView):
    """
    Get bikes similar to a specific bike.
    
    Query Parameters:
    - limit: Number of similar bikes (default: 6)
    
    * Requires: None (public access)
    * Returns: List of similar bikes with scores and reasons
    """
    serializer_class = BikeRecommendationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable pagination
    
    def get_queryset(self):
from django.contrib import messages
from django.shortcuts import render, redirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import Bike
from .serializers import BikeSerializer, BikehostCreateSerializer, BikeRecommendationSerializer
from .filters import BikeFilter
from .forms import BikehostCreateForm
from .permissions import IshostOrAdmin
from .recommendations import get_recommendations_for_user, get_popular_bikes, get_similar_bikes


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
    Create a new bike listing for hosts, with admin approval required.

    * Requires: Authentication
    * Returns: Newly created bike data or renders a form for non-API requests
    """
    queryset = Bike.objects.all()
    serializer_class = BikehostCreateSerializer  # For API requests
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user, availability_status=False, is_approved=False, is_featured=False)

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return super().post(request, *args, **kwargs)
        form = BikehostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            bike = form.save(commit=False)
            bike.host = request.user
            bike.availability_status = False
            bike.is_approved = False
            bike.is_featured = False
            bike.save()
            messages.success(request, "Your bike listing has been submitted. An admin will review it soon.")
            return redirect('users:bike-host-dashboard')
        return render(request, 'bikes/bike_create_host.html', {'form': form})

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        form = BikehostCreateForm()
        return render(request, 'bikes/bike_create_host.html', {'form': form})

class BikeUpdateView(generics.UpdateAPIView):
    """
    Update an existing bike listing.

    * Requires: Authentication (only host or admin)
    * Returns: Updated bike data or renders a form for non-API requests
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IshostOrAdmin]

    def get_serializer_class(self):
        # Use BikehostCreateSerializer for hosts, BikeSerializer for admins
        if self.request.user == self.get_object().host and not self.request.user.is_superuser:
            return BikehostCreateSerializer
        return BikeSerializer

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        bike = self.get_object()
        form = BikehostCreateForm(instance=bike)
        return render(request, 'bikes/bike_update_host.html', {'form': form, 'bike': bike})

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return super().put(request, *args, **kwargs)
        bike = self.get_object()
        form = BikehostCreateForm(request.POST, request.FILES, instance=bike)
        if form.is_valid():
            form.save()
            messages.success(request, "Your bike listing has been updated successfully.")
            return redirect('users:bike-host-dashboard')
        return render(request, 'bikes/bike_update_host.html', {'form': form, 'bike': bike})

class BikeDeleteView(generics.DestroyAPIView):
    """
    Delete a bike listing.

    * Requires: Authentication (only host or admin)
    * Returns: Success message or renders confirmation page for non-API requests
    """
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IshostOrAdmin]

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        bike = self.get_object()
        return render(request, 'bikes/bike_delete_confirm.html', {'bike': bike})

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            return super().delete(request, *args, **kwargs)
        bike = self.get_object()
        bike_name = bike.name
        bike.delete()
        messages.success(request, f"Bike listing '{bike_name}' has been deleted successfully.")
        return redirect('users:bike-host-dashboard')


class BikeRecommendationsView(generics.ListAPIView):
    """
    Get personalized bike recommendations for the authenticated user.
    
    Query Parameters:
    - strategy: 'popularity', 'content', 'collaborative', or 'hybrid' (default: 'hybrid')
    - limit: Number of recommendations (default: 6)
    
    * Requires: None (works for both authenticated and anonymous users)
    * Returns: List of recommended bikes with scores and reasons
    """
    serializer_class = BikeRecommendationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable pagination for recommendations
    
    def get_queryset(self):
        user = self.request.user if self.request.user.is_authenticated else None
        strategy = self.request.query_params.get('strategy', 'hybrid')
        limit = int(self.request.query_params.get('limit', 6))
        
        if user:
            recommendations = get_recommendations_for_user(user, strategy=strategy, limit=limit)
        else:
            # For anonymous users, show popular bikes
            recommendations = get_popular_bikes(limit=limit)
        
        return recommendations


class SimilarBikesView(generics.ListAPIView):
    """
    Get bikes similar to a specific bike.
    
    Query Parameters:
    - limit: Number of similar bikes (default: 6)
    
    * Requires: None (public access)
    * Returns: List of similar bikes with scores and reasons
    """
    serializer_class = BikeRecommendationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable pagination
    
    def get_queryset(self):
        bike_id = self.kwargs.get('pk')
        limit = int(self.request.query_params.get('limit', 6))
        
        similar_bikes = get_similar_bikes(bike_id=bike_id, limit=limit)
        return similar_bikes