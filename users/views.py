from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage  # Import default_storage for debugging

from bikes.models import Bike
from bookings.models import Booking
from testimonials.models import Testimonial
from admin_panel.models import ContactMessage  # Import the new ContactMessage model
from .filters import UserFilter
from .models import User, OwnerProfile, BikeOwnerRequest
from .serializers import UserSerializer, OwnerProfileSerializer, LoginSerializer, BikeOwnerRequestSerializer
from .permissions import IsUserOrReadOnly, IsOwnerOrAdmin


class DashboardView(APIView):
    """
    Display the user dashboard with metrics, recent activity, feedback, and bike owner options.

    * Requires: Authentication
    * Returns: Renders the dashboard template for non-API requests
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        user = request.user
        total_bookings = Booking.objects.filter(user=user).count()
        active_bookings = Booking.objects.filter(user=user, status='confirmed').count()
        upcoming_bookings = Booking.objects.filter(user=user, start_date__gt=timezone.now()).count()
        recent_bookings = Booking.objects.filter(user=user).order_by('-created_at')[:5]
        recent_feedback = Testimonial.objects.filter(user=user).order_by('-created_at')[:5]

        bike_owner_request = BikeOwnerRequest.objects.filter(user=user).order_by('-requested_at').first()

        context = {
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'upcoming_bookings': upcoming_bookings,
            'recent_bookings': recent_bookings,
            'recent_feedback': recent_feedback,
            'bike_owner_request': bike_owner_request,
            'user_bikes': Bike.objects.filter(owner=user) if user.is_owner else None,
        }
        return render(request, 'users/dashboard.html', context)


class BikeOwnerDashboardView(APIView):
    """
    Display the bike owner dashboard with detailed metrics, bike listings, pending bookings, and booking history.

    * Requires: Authentication and is_owner = True
    * Returns: Renders the owner dashboard template for non-API requests
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if not request.user.is_owner:
            messages.error(request, "You are not authorized to access the owner dashboard.")
            return redirect('users:dashboard')

        user = request.user
        user_bikes = Bike.objects.filter(owner=user)
        owner_profile = OwnerProfile.objects.get_or_create(user=user)[0]

        # Pending booking requests for the owner's bikes
        pending_bookings = Booking.objects.filter(
            bike__owner=user,
            status='pending'
        ).order_by('-created_at')[:5]

        # Recent confirmed or completed bookings for the owner's bikes
        recent_bookings = Booking.objects.filter(
            bike__owner=user,
            status__in=['confirmed', 'completed']
        ).order_by('-created_at')[:5]

        # Calculate active listings (bikes that are available and approved)
        active_listings = user_bikes.filter(availability_status=True, is_approved=True).count()

        context = {
            'user_bikes': user_bikes,
            'total_earnings': owner_profile.total_earnings,
            'total_bookings': owner_profile.total_bookings,
            'pending_bookings': pending_bookings,
            'recent_bookings': recent_bookings,
            'active_listings': active_listings,
        }
        return render(request, 'users/bike_owner_dashboard.html', context)


class BikeOwnerRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if request.user.is_owner:
            messages.info(request, "You are already a bike owner.")
            return redirect('users:dashboard')

        bike_owner_request = BikeOwnerRequest.objects.filter(user=request.user).order_by('-requested_at').first()
        if bike_owner_request and bike_owner_request.status == 'approved':
            messages.info(request,
                          "Your request has been approved. You can now list your bike (dashboard to be implemented).")
            return redirect('users:dashboard')
        elif bike_owner_request and bike_owner_request.status == 'pending':
            messages.info(request, "You already have a pending request. Please wait for admin review.")
            return redirect('users:dashboard')

        initial_data = {
            'bike_make': '',
            'bike_model': '',
            'bike_year': '',
            'bike_registration_number': '',
        }
        if bike_owner_request and bike_owner_request.status == 'rejected':
            initial_data.update({
                'bike_make': bike_owner_request.bike_make or '',
                'bike_model': bike_owner_request.bike_model or '',
                'bike_year': bike_owner_request.bike_year or '',
                'bike_registration_number': bike_owner_request.bike_registration_number or '',
            })
        context = {
            'initial_data': initial_data,
            'current_year': timezone.now().year,
            'bike_owner_request': bike_owner_request
        }
        print("Context for bike_owner_request.html:", context)
        return render(request, 'users/bike_owner_request.html', context)

    def post(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if request.user.is_owner:
            messages.info(request, "You are already a bike owner.")
            return redirect('users:dashboard')

        bike_owner_request = BikeOwnerRequest.objects.filter(user=request.user).order_by('-requested_at').first()
        if bike_owner_request and bike_owner_request.status == 'approved':
            messages.info(request,
                          "Your request has been approved. You can now list your bike (dashboard to be implemented).")
            return redirect('users:dashboard')
        elif bike_owner_request and bike_owner_request.status == 'pending':
            messages.info(request, "You already have a pending request. Please wait for admin review.")
            return redirect('users:dashboard')

        serializer_data = request.POST.copy()
        serializer_data.update(request.FILES)
        serializer = BikeOwnerRequestSerializer(data=serializer_data, context={'request': request})
        if serializer.is_valid():
            if bike_owner_request and bike_owner_request.status == 'rejected':
                bike_owner_request.bike_make = serializer.validated_data['bike_make']
                bike_owner_request.bike_model = serializer.validated_data['bike_model']
                bike_owner_request.bike_year = serializer.validated_data['bike_year']
                bike_owner_request.bike_registration_number = serializer.validated_data['bike_registration_number']
                if 'registration_certificate' in request.FILES:
                    bike_owner_request.registration_certificate = request.FILES['registration_certificate']
                if 'insurance_certificate' in request.FILES:
                    bike_owner_request.insurance_certificate = request.FILES['insurance_certificate']
                if 'id_proof' in request.FILES:
                    bike_owner_request.id_proof = request.FILES['id_proof']
                if 'bike_photos' in request.FILES:
                    bike_owner_request.bike_photos = request.FILES['bike_photos']
                bike_owner_request.status = 'pending'
                bike_owner_request.requested_at = timezone.now()
                bike_owner_request.reviewed_at = None
                bike_owner_request.admin_notes = None
                bike_owner_request.save()
                messages.success(request, "Your request has been updated and resubmitted for review.")
            else:
                validated_data = serializer.validated_data
                request_instance = BikeOwnerRequest(
                    user=request.user,
                    bike_make=validated_data['bike_make'],
                    bike_model=validated_data['bike_model'],
                    bike_year=validated_data['bike_year'],
                    bike_registration_number=validated_data['bike_registration_number'],
                    registration_certificate=validated_data['registration_certificate'],
                    insurance_certificate=validated_data['insurance_certificate'],
                    id_proof=validated_data['id_proof'],
                    bike_photos=validated_data['bike_photos'],
                )
                # Debug: Print MEDIA_ROOT and storage location before saving
                print("MEDIA_ROOT before saving:", settings.MEDIA_ROOT)
                print("Default Storage Location:", default_storage.location)
                request_instance.save()
                # Debug: Print the absolute file paths after saving
                print("Saved Registration Certificate Path:", request_instance.registration_certificate.path)
                print("Saved Insurance Certificate Path:", request_instance.insurance_certificate.path)
                print("Saved ID Proof Path:", request_instance.id_proof.path)
                print("Saved Bike Photos Path:", request_instance.bike_photos.path)
                admin_email = 'admin@example.com'
                send_mail(
                    'New Bike Owner Request',
                    f'A new bike owner request has been submitted by {request.user.username}. Review it at /admin/users/bikeownerrequest/{request_instance.id}/change/.',
                    'from@example.com',
                    [admin_email],
                    fail_silently=True,
                )
                messages.success(request, "Your request has been submitted. An admin will review it soon.")
            return redirect('users:dashboard')
        context = {
            'errors': serializer.errors,
            'initial_data': request.POST if request.POST else {'bike_make': '', 'bike_model': '', 'bike_year': '',
                                                               'bike_registration_number': ''},
            'current_year': timezone.now().year,
            'bike_owner_request': bike_owner_request
        }
        print("Context for bike_owner_request.html (POST error):", context)
        print("Serializer errors:", serializer.errors)
        return render(request, 'users/bike_owner_request.html', context)


class AdminBikeOwnerRequestListView(generics.ListAPIView):
    queryset = BikeOwnerRequest.objects.all()
    serializer_class = BikeOwnerRequestSerializer
    permission_classes = [IsAdminUser]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        requests = self.get_queryset()
        return render(request, 'users/admin_bike_owner_request_list.html', {'requests': requests})

    def post(self, request, pk):
        request_instance = get_object_or_404(BikeOwnerRequest, pk=pk)
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        if action == 'approve':
            request_instance.approve()
            send_mail(
                'Bike Owner Request Approved',
                f'Your request to become a bike owner has been approved. You can now list your bike (dashboard to be implemented).',
                'from@example.com',
                [request_instance.user.email],
                fail_silently=True,
            )
            messages.success(request, f"Request for {request_instance.user.username} approved.")
        elif action == 'reject':
            request_instance.reject(notes)
            send_mail(
                'Bike Owner Request Rejected',
                f'Your request to become a bike owner has been rejected. Reason: {notes}. You can update and resubmit your request.',
                'from@example.com',
                [request_instance.user.email],
                fail_silently=True,
            )
            messages.success(request, f"Request for {request_instance.user.username} rejected.")
        return redirect('users:admin-bike-owner-request-list')


class UserListView(generics.ListAPIView):
    """
    List all registered users.

    * Requires: Admin authentication for API, template rendering for non-API
    * Returns: JSON list of user data for API, renders user list template for non-API
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON for API requests (e.g., /api/user/)
            return super().get(request, *args, **kwargs)
        # Render template for non-API requests (e.g., /user/)
        users = self.get_queryset()
        return render(request, 'users/user_list.html', {'users': users})


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    View and update the authenticated user's profile.

    * Requires: Authentication (only the user themselves can view/modify their profile)
    * Returns: JSON user data for API, renders template for non-API with form handling
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsUserOrReadOnly]

    def get_object(self):
        # Return the authenticated user instead of looking up by PK
        return self.request.user

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON for API requests
            return super().get(request, *args, **kwargs)
        # Render template for non-API requests
        user = self.get_object()
        return render(request, 'users/user_detail.html', {'user': user})

    def post(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Handle API POST request
            return super().post(request, *args, **kwargs)
        # Handle form submission for non-API requests
        user = self.request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number) or None
        user.address = request.POST.get('address', user.address) or None
        user.date_of_birth = request.POST.get('date_of_birth', user.date_of_birth) or None
        user.bio = request.POST.get('bio', user.bio) or None

        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        try:
            user.save()
            messages.success(request, "Profile updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")

        return redirect('users:user-detail')


class RegisterUserView(APIView):
    """
    Register a new user.

    * Requires: None (public access) for API, template rendering for non-API
    * Returns: JSON with token and user data for API, renders registration form or redirects for non-API
    """
    permission_classes = [AllowAny]
    throttle_scope = 'register'

    def post(self, request):
        serializer = UserSerializer(data=request.data if request.content_type == 'application/json' else request.POST)

        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
                # Return JSON for API requests (e.g., /api/user/register/)
                return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                # Handle non-API POST (e.g., form submission to /register/)
                login(request, user)
                messages.success(request, f"Welcome, {user.username}! Registration successful.")
                return redirect('home')  # Redirect to homepage after successful registration
        else:
            if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
                # Return JSON errors for API requests
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Render template with errors for non-API requests
                return render(request, 'users/register.html', {'errors': serializer.errors}, status=400)

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # Render template for non-API GET requests (e.g., /register/)
        return render(request, 'users/register.html')


class LoginView(APIView):
    """
    Log in an existing user.

    * Requires: None (public access) for API, template rendering for non-API
    * Returns: JSON with token and user data for API, renders login form or redirects for non-API
    """
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data if request.content_type == 'application/json' else request.POST)
        if serializer.is_valid():
            user = authenticate(username=request.data.get('username') or request.POST.get('username'),
                                password=request.data.get('password') or request.POST.get('password'))
            if user:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
                    # Return JSON for API requests (e.g., /api/user/login/)
                    return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_200_OK)
                else:
                    # Handle non-API POST (e.g., form submission to /login/)
                    messages.success(request, f"Welcome back, {user.username}!")
                    return redirect('home')  # Redirect to homepage after successful login
            if request.path.startswith('/api/'):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            return render(request, 'users/login.html', {'errors': {"error": "Invalid credentials"}})
        else:
            if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
                # Return JSON errors for API requests
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Render template with errors for non-API requests
                return render(request, 'users/login.html', {'errors': serializer.errors})

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # Render template for non-API GET requests (e.g., /login/)
        return render(request, 'users/login.html')


class LogoutView(APIView):
    """
    Log out an authenticated user.

    * Requires: Authentication
    * Returns: JSON success message for API, redirects to homepage for non-API
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if a token exists before attempting to delete
        try:
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            else:
                # Create a new token if none exists (optional, for robustness)
                token, created = Token.objects.get_or_create(user=request.user)
                if not created:
                    token.delete()
        except Token.DoesNotExist:
            print("No token found for user, proceeding with logout.")

        logout(request)

        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON for API requests (e.g., /api/user/logout/)
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        else:
            # Redirect to homepage for non-API requests (e.g., form submission to /logout/)
            messages.success(request, f"You have been logged out, {request.user.username}.")
            return redirect('home')  # Redirect to homepage after logout

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # Render template for non-API GET requests (e.g., /logout/)
        return render(request, 'users/logout.html', {'username': request.user.username})


class OwnerProfileListView(generics.ListCreateAPIView):
    """
    List all owner profiles or create a new one.

    * Requires: Authentication (admin for listing, user for creation) for API, template rendering for non-API
    * Returns: JSON list of owner profiles or new profile data for API, renders template for non-API
    """
    queryset = OwnerProfile.objects.all()
    serializer_class = OwnerProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        profiles = self.get_queryset()
        return render(request, 'users/owner_profile_list.html', {'profiles': profiles})


class OwnerProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an owner profile.

    * Requires: Authentication (only owner or admin can view/modify) for API, template rendering for non-API
    * Returns: JSON owner profile data for API, renders template for non-API
    """
    queryset = OwnerProfile.objects.all()
    serializer_class = OwnerProfileSerializer
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        profile = self.get_object()
        return render(request, 'users/owner_profile_detail.html', {'profile': profile})


class ContactView(APIView):
    """
    Display contact information or handle contact form submissions.

    * Requires: None (public access)
    * Returns: JSON response for API requests, renders template for non-API requests
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # Render the contact template (similar to the contact section in home.html)
        return render(request, 'users/contact.html')

    def post(self, request):
        # Determine if this is an API request
        is_api_request = request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', '')

        # Extract form data (handle both API and non-API requests)
        if is_api_request:
            data = request.data
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            contact_number = data.get('contact_number', '').strip()
            message = data.get('message', '').strip()
        else:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            contact_number = request.POST.get('contact_number', '').strip()
            message = request.POST.get('message', '').strip()

        # Basic validation
        errors = {}
        if not name:
            errors['name'] = "Name is required."
        if not email:
            errors['email'] = "Email is required."
        elif "@" not in email or "." not in email:
            errors['email'] = "Please enter a valid email address."
        if not contact_number:
            errors['contact_number'] = "Contact number is required."
        elif not contact_number.replace("+", "").replace(" ", "").isdigit():
            errors['contact_number'] = "Contact number must contain only digits (and optionally a '+' prefix)."
        elif len(contact_number) < 7 or len(contact_number) > 15:
            errors['contact_number'] = "Contact number must be between 7 and 15 characters long."
        if not message:
            errors['message'] = "Message is required."
        elif len(message) < 10:
            errors['message'] = "Message must be at least 10 characters long."

        if errors:
            if is_api_request:
                return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
            return render(request, 'users/contact.html', {'errors': errors, 'form_data': request.POST})

        # Save the contact message to the database
        try:
            contact_message = ContactMessage(
                name=name,
                email=email,
                contact_number=contact_number,
                message=message
            )
            contact_message.save()

            # Send email notification to admin
            admin_email = 'admin@gmail.com'
            try:
                send_mail(
                    'New Contact Message',
                    f'A new contact message has been submitted by {name} ({email}).\n\n'
                    f'Contact Number: {contact_number}\n\n'
                    f'Message:\n{message}\n\n'
                    f'Review it at /admin/admin_panel/contactmessage/{contact_message.id}/change/.',
                    'easymotoservices@gmail.com',
                    [admin_email],
                    fail_silently=False,
                )
            except Exception as e:
                error_message = f"Error sending email notification to admin: {str(e)}"
                if is_api_request:
                    return Response({"detail": "Message saved, but " + error_message}, status=status.HTTP_201_CREATED)
                messages.error(request, error_message)
                print(f"Email sending failed: {str(e)}")

            if is_api_request:
                return Response({"detail": f"Thank you, {name}! Your message has been received."}, status=status.HTTP_201_CREATED)
            messages.success(request, f"Thank you, {name}! Your message has been received. We’ll get back to you soon.")
            return redirect('home')  # Redirect to homepage after submission
        except Exception as e:
            error_message = f"Error submitting your message: {str(e)}"
            if is_api_request:
                return Response({"detail": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            messages.error(request, error_message)
            return render(request, 'users/contact.html', {'form_data': request.POST})