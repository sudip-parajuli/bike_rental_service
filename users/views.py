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
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.views import View

from bikes.models import Bike
from bookings.models import Booking
from testimonials.models import Testimonial
from admin_panel.models import ContactMessage
from payment.models import Payment
from .filters import UserFilter
from .models import User, hostProfile, BikehostRequest
from .serializers import UserSerializer, hostProfileSerializer, LoginSerializer, BikehostRequestSerializer
from .permissions import IsUserOrReadOnly, IshostOrAdmin
from bikes.recommendations import get_recommendations_for_user
from .forms import RegisterForm


class HomeView(View):
    """
    Custom home view that redirects authenticated users to dashboard
    and shows homepage to anonymous users.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        return render(request, 'home.html')


class DashboardView(APIView):
    """
    Display the user dashboard with metrics, recent activity, feedback, and bike host options.

    * Requires: Authentication
    * Returns: Renders the dashboard template for non-API requests
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        user = request.user
        
        # Metrics
        active_bookings = Booking.objects.filter(user=user, status='confirmed').count()
        total_bookings = Booking.objects.filter(user=user).count()
        upcoming_bookings = Booking.objects.filter(user=user, status='confirmed', start_date__gt=timezone.now()).count()
        
        # Payments
        pending_payments_count = Payment.objects.filter(booking__user=user, status='pending').count()
        outstanding_payment_amount = Payment.objects.filter(booking__user=user, status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
        last_payment = Payment.objects.filter(booking__user=user, status='completed').order_by('-created_at').first()
        
        # Next Pickup
        next_pickup = Booking.objects.filter(user=user, status='confirmed', start_date__gt=timezone.now()).order_by('start_date').first()
        
        # History
        booking_history = Booking.objects.filter(user=user).order_by('-created_at')
        
        # Recommendations
        recommended_bikes = get_recommendations_for_user(user, limit=4)
        
        # Host Request Status
        bike_host_request = BikehostRequest.objects.filter(user=user).order_by('-requested_at').first()
        
        # Special Offer Logic
        completed_rentals_count = Booking.objects.filter(user=user, status='completed').count()
        show_special_offer = completed_rentals_count > 0 and completed_rentals_count % 5 == 0

        context = {
            'user': user,
            'active_bookings': active_bookings,
            'total_bookings': total_bookings,
            'upcoming_bookings': upcoming_bookings,
            'pending_payments_count': pending_payments_count,
            'outstanding_payment_amount': outstanding_payment_amount,
            'last_payment': last_payment,
            'next_pickup': next_pickup,
            'booking_history': booking_history,
            'recommended_bikes': recommended_bikes,
            'bike_host_request': bike_host_request,
            'show_special_offer': show_special_offer,
        }
        return render(request, 'users/dashboard.html', context)


class BikehostDashboardView(APIView):
    """
    Display the bike host dashboard.

    * Requires: Authentication and Host/Admin permissions
    * Returns: Renders the host dashboard template
    """
    permission_classes = [IsAuthenticated, IshostOrAdmin]

    def get(self, request):
        if request.path.startswith('/api/'):
             return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Add host specific logic here
        user_bikes = Bike.objects.filter(host=request.user)
        
        # Fetch bookings for the host's bikes
        host_bookings = Booking.objects.filter(bike__in=user_bikes).order_by('-created_at')
        
        # Pending bookings (requests)
        pending_bookings = host_bookings.filter(status='pending')
        
        # Recent bookings (confirmed, completed, cancelled)
        recent_bookings = host_bookings.exclude(status='pending')
        
        # Calculate total earnings from completed and paid bookings
        total_earnings = host_bookings.filter(
            status='completed', 
            payment_status='paid'
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Active listings count
        active_listings = user_bikes.filter(availability_status=True).count()
        
        context = {
            'user': request.user,
            'user_bikes': user_bikes,
            'pending_bookings': pending_bookings,
            'recent_bookings': recent_bookings,
            'total_earnings': total_earnings,
            'active_listings': active_listings,
            'total_bookings': host_bookings.count(),
        }
        return render(request, 'users/bike_host_dashboard.html', context)


class BikehostRequestView(APIView):
    """
    Handle requests to become a bike host.

    * Requires: Authentication
    * Returns: Renders the bike host request form
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if request.user.is_host:
            messages.info(request, "You are already a bike host.")
            return redirect('users:dashboard')

        bike_host_request = BikehostRequest.objects.filter(user=request.user).order_by('-requested_at').first()
        if bike_host_request and bike_host_request.status == 'approved':
            messages.info(request,
                          "Your request has been approved. You can now list your bike (dashboard to be implemented).")
            return redirect('users:dashboard')
        elif bike_host_request and bike_host_request.status == 'pending':
            messages.info(request, "You already have a pending request. Please wait for admin review.")
            return redirect('users:dashboard')

        initial_data = {
            'bike_make': '',
            'bike_model': '',
            'bike_year': '',
            'bike_registration_number': '',
        }
        if bike_host_request and bike_host_request.status == 'rejected':
            initial_data.update({
                'bike_make': bike_host_request.bike_make or '',
                'bike_model': bike_host_request.bike_model or '',
                'bike_year': bike_host_request.bike_year or '',
                'bike_registration_number': bike_host_request.bike_registration_number or '',
            })
        context = {
            'initial_data': initial_data,
            'current_year': timezone.now().year,
            'bike_host_request': bike_host_request
        }
        return render(request, 'users/bike_host_request.html', context)

    def post(self, request):
        if request.path.startswith('/api/'):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if request.user.is_host:
            messages.info(request, "You are already a bike host.")
            return redirect('users:dashboard')

        bike_host_request = BikehostRequest.objects.filter(user=request.user).order_by('-requested_at').first()
        if bike_host_request and bike_host_request.status == 'approved':
            messages.info(request,
                          "Your request has been approved. You can now list your bike (dashboard to be implemented).")
            return redirect('users:dashboard')
        elif bike_host_request and bike_host_request.status == 'pending':
            messages.info(request, "You already have a pending request. Please wait for admin review.")
            return redirect('users:dashboard')

        serializer_data = request.POST.copy()
        serializer_data.update(request.FILES)
        serializer = BikehostRequestSerializer(data=serializer_data, context={'request': request})
        if serializer.is_valid():
            if bike_host_request and bike_host_request.status == 'rejected':
                bike_host_request.bike_make = serializer.validated_data['bike_make']
                bike_host_request.bike_model = serializer.validated_data['bike_model']
                bike_host_request.bike_year = serializer.validated_data['bike_year']
                bike_host_request.bike_registration_number = serializer.validated_data['bike_registration_number']
                if 'registration_certificate' in request.FILES:
                    bike_host_request.registration_certificate = request.FILES['registration_certificate']
                if 'insurance_certificate' in request.FILES:
                    bike_host_request.insurance_certificate = request.FILES['insurance_certificate']
                if 'id_proof' in request.FILES:
                    bike_host_request.id_proof = request.FILES['id_proof']
                if 'bike_photos' in request.FILES:
                    bike_host_request.bike_photos = request.FILES['bike_photos']
                bike_host_request.status = 'pending'
                bike_host_request.requested_at = timezone.now()
                bike_host_request.reviewed_at = None
                bike_host_request.admin_notes = None
                bike_host_request.save()
                messages.success(request, "Your request has been updated and resubmitted for review.")
            else:
                validated_data = serializer.validated_data
                request_instance = BikehostRequest(
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
                request_instance.save()
                admin_email = 'sparajuli802@gmail.com'
                send_mail(
                    'New Bike host Request',
                    f'A new bike host request has been submitted by {request.user.username}. Review it at /admin/users/bikehostrequest/{request_instance.id}/change/.',
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
            'bike_host_request': bike_host_request
        }
        return render(request, 'users/bike_host_request.html', context)


class AdminBikehostRequestListView(generics.ListAPIView):
    queryset = BikehostRequest.objects.all()
    serializer_class = BikehostRequestSerializer
    permission_classes = [IsAdminUser]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        requests = self.get_queryset()
        return render(request, 'users/admin_bike_host_request_list.html', {'requests': requests})

    def post(self, request, pk):
        request_instance = get_object_or_404(BikehostRequest, pk=pk)
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        if action == 'approve':
            request_instance.approve()
            send_mail(
                'Bike host Request Approved',
                f'Your request to become a bike host has been approved. You can now list your bike (dashboard to be implemented).',
                'from@example.com',
                [request_instance.user.email],
                fail_silently=True,
            )
            messages.success(request, f"Request for {request_instance.user.username} approved.")
        elif action == 'reject':
            request_instance.reject(notes)
            send_mail(
                'Bike host Request Rejected',
                f'Your request to become a bike host has been rejected. Reason: {notes}. You can update and resubmit your request.',
                'from@example.com',
                [request_instance.user.email],
                fail_silently=True,
            )
            messages.success(request, f"Request for {request_instance.user.username} rejected.")
        return redirect('users:admin-bike-host-request-list')


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



class RegisterView(View):
    """
    Register a new user (Browser-based).
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'users/register.html', {'form': RegisterForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Account created successfully! Welcome, {user.username}.")
            return redirect('home')
        
        return render(request, 'users/register.html', {'form': form, 'errors': form.errors})


class LoginView(View):
    """
    Log in an existing user (Browser-based).
    For API login, use /api/auth/login/.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'users/login.html')

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')

        # Standard Django form handling would be better, but keeping custom logic for now
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
             return render(request, 'users/login.html', {'errors': {'error': "Please provide both username and password."}})

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if user.is_staff or user.is_superuser:
                return redirect('admin_panel:dashboard')
            
            # Check for next parameter
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            return render(request, 'users/login.html', {'errors': {'error': "Invalid credentials"}})


class LogoutView(APIView):
    """
    Log out an authenticated user.

    * Requires: Authentication
    * Returns: JSON success message for API, redirects to homepage for non-API
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
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


class hostProfileListView(generics.ListCreateAPIView):
    """
    List all host profiles or create a new one.

    * Requires: Authentication (admin for listing, user for creation) for API, template rendering for non-API
    * Returns: JSON list of host profiles or new profile data for API, renders template for non-API
    """
    queryset = hostProfile.objects.all()
    serializer_class = hostProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        profiles = self.get_queryset()
        return render(request, 'users/host_profile_list.html', {'profiles': profiles})


class hostProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an host profile.

    * Requires: Authentication (only host or admin can view/modify) for API, template rendering for non-API
    * Returns: JSON host profile data for API, renders template for non-API
    """
    queryset = hostProfile.objects.all()
    serializer_class = hostProfileSerializer
    permission_classes = [IshostOrAdmin]
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        profile = self.get_object()
        return render(request, 'users/host_profile_detail.html', {'profile': profile})


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

from .forms import PhoneNumberForm

class AddPhoneNumberView(APIView):
    """
    View to enforce mobile number collection.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.phone_number:
            return redirect('users:dashboard')
        form = PhoneNumberForm(instance=request.user)
        return render(request, 'users/add_phone_number.html', {'form': form})

    def post(self, request):
        if request.user.phone_number:
            return redirect('users:dashboard')
        
        form = PhoneNumberForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Phone number added successfully.")
            return redirect('users:dashboard')
        
        return render(request, 'users/add_phone_number.html', {'form': form})