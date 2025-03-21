# Django Project - [Bike Rental Service] 🐍🛠

    The Bike Rental Service is a web-based platform designed to streamline the process of renting bikes online.
    Users can browse available bikes, make bookings, view testimonials, and complete payments using PayPal or eSewa.
    Bike owners can submit their bikes for listing, and admins can manage the platform efficiently.

-----------------------------------------------------------------------------------------------------------------------

## Features ✨

    # Users
        -User Registration and Authentication (Token-based Authentication using JWT)
        -Browse and Search Bikes
        -Make a Booking with start and end dates
        -Payment Integration
        -View Testimonials and submit feedback
        -User Dashboard Access

    #Bike Owners
       - Bike Owner Registration
       - Bike Listing Submission (with document uploads: registration certificate, insurance certificate, ID proof, and bike photos)
       - Dashboard Access for managing listed bikes

    #Admin
       -Manage Bikes (approve/reject bikes submitted by owners)
       -Manage Bookings and User Data
       -View Feedback and Testimonials

------------------------------------------------------------------------------------------------------------------------

## Technologies Used 🛠

# Backend:

    -Python
    -Django (including Django REST Framework - DRF)
    -PostgreSQL for database management
    -JWT Authentication for secure login

# Frontend:

    -HTML, CSS, Bootstrap 5
    JavaScript for interactivity

------------------------------------------------------------------------------------------------------------------------

## Payment Integration

    # PayPal:
        - The platform uses PayPal for secure online payments. Configure your PayPal credentials in the .env file.
    
    # eSewa:
         - The eSewa payment gateway allows users in Nepal to pay online. Set up the necessary merchant credentials and URLs.

------------------------------------------------------------------------------------------------------------------------

## Installation and setup 🛠 
    Follow these steps to run the project locally.

    1. Clone the Repository
    2. Create and Activate a Virtual Environment
    3. Install Requirements
    4. Set Up the Database
        PostgreSQL Configuration: Update the DATABASES setting in settings.py with your PostgreSQL credentials.
    5. Apply Migrations
    6. Create Superuser (Admin)
    7. Run the Development Server
        Access the app at: http://localhost:8000/
------------------------------------------------------------------------------------------------------------------------

## API Documentation 📄
    This project includes API documentation using Swagger and Redoc.

        Swagger: http://127.0.0.1:8000/api/swagger/
        Redoc: http://127.0.0.1:8000/api/redoc/

------------------------------------------------------------------------------------------------------------------------

## Directory Structure
    BikeRentalService/  
        |-- bookings/         # Booking app (models, views, serializers, URLs)  
        |-- bikes/            # Bike management app  
        |-- users/            # User authentication and management  
        |-- testimonial/      # User feedback and testimonials  
        |-- admin_panel/      # Admin-specific features  
        |-- media/            # Uploaded documents (e.g., bike photos, certificates)  
        |-- templates/        # HTML templates  
        |-- static/           # CSS, JS, images  
        |-- manage.py         # Django project entry point  

------------------------------------------------------------------------------------------------------------------------
## Endpoints 📄
---

### API Endpoints (JSON Responses)

#### Users App (Authentication, User, and Owner Management)
- **POST** `/api/user/register/` - Register a new user  
- **POST** `/api/user/login/` - Log in a user  
- **POST** `/api/user/logout/` - Log out a user  
- **GET** `/api/user/` - Get the list of users  
- **GET** `/api/user/profile/` - Get user profile details  
- **GET** `/api/user/owners/` - List all bike owners  
- **GET** `/api/user/owners/<int:pk>/` - Retrieve a bike owner's details  
- **GET** `/api/user/dashboard/` - View user dashboard  
- **GET** `/api/user/dashboard/owner/` - View bike owner dashboard  
- **POST** `/api/user/contact/` - Send a contact message  
- **POST** `/api/user/bike-owner-request/` - Request bike owner verification  
- **GET** `/api/user/admin/bike-owner-requests/` - Admin: View bike owner requests  
- **GET** `/api/user/admin/bike-owner-requests/<int:pk>/` - Admin: View specific bike owner request  

---

#### Testimonials App (Feedback and Reviews)
- **GET** `/api/testimonial/` - List all testimonials  
- **GET** `/api/testimonial/<int:pk>/` - Retrieve a specific testimonial  
- **POST** `/api/testimonial/create/` - Create a new testimonial  
- **PUT** `/api/testimonial/<int:pk>/update/` - Update an existing testimonial  
- **DELETE** `/api/testimonial/<int:pk>/delete/` - Delete a testimonial  

---

#### Payment App (Payment Processing)
- **GET** `/api/payment/` - List all payments  
- **GET** `/api/payment/<int:pk>/` - Retrieve payment details  
- **POST** `/api/payment/paypal/<int:booking_id>/<str:amount>/` - Process PayPal payment  
- **POST** `/api/payment/esewa/<int:booking_id>/<str:amount>/` - Process eSewa payment  
- **GET** `/api/payment/esewa-success/` - eSewa payment success endpoint  
- **GET** `/api/payment/esewa-failure/` - eSewa payment failure endpoint  
- **GET** `/api/payment/paypal-return/` - PayPal payment success endpoint  
- **GET** `/api/payment/paypal-cancel/` - PayPal payment cancellation endpoint  
- **POST** `/api/payment/paypal-ipn/` - PayPal IPN endpoint for instant notifications  

---

#### Bookings App (Reservation Management)
- **GET** `/api/booking/` - List all bookings  
- **GET** `/api/booking/<int:pk>/` - Retrieve booking details  
- **POST** `/api/booking/create/` - Create a new booking  
- **PUT** `/api/booking/<int:pk>/update/` - Update an existing booking  
- **DELETE** `/api/booking/<int:pk>/delete/` - Delete a booking  
- **POST** `/api/booking/<int:pk>/payment-select/` - Select payment method for a booking  
- **POST** `/api/booking/<int:pk>/approve/` - Approve a booking (admin only)  
- **POST** `/api/booking/<int:pk>/reject/` - Reject a booking (admin only)  
- **POST** `/api/booking/<int:pk>/complete/` - Mark a booking as completed  

---

#### Bikes App (Bike Management)
- **GET** `/api/bike/` - List all bikes  
- **GET** `/api/bike/<int:pk>/` - Retrieve bike details  
- **POST** `/api/bike/create/` - Add a new bike (Bike Owner only)  
- **PUT** `/api/bike/<int:pk>/update/` - Update bike information  
- **DELETE** `/api/bike/<int:pk>/delete/` - Delete a bike  

---

#### Swagger & API Authentication
- **Swagger UI**: `/api/swagger/` - Interactive API Documentation  
- **ReDoc UI**: `/api/redoc/` - API documentation (Redoc format)  
- **API Authentication**: `/api-auth/` - Authentication endpoints for session-based login  

---

### Template-Based (HTML) Endpoints

#### Bikes App (HTML Views)
- **GET** `/bikes/` - View list of bikes   

---

#### Bookings App (HTML Views)
- **GET** `/bookings/` - View list of bookings

---

#### Testimonials App (HTML Views)
- **GET** `/testimonials/` - View list of testimonials

---

#### Users App (HTML Views)
- **GET** `/users/register/` - Form to register a new user  
- **GET** `/users/login/` - Form to log in a user  
- **GET** `/users/logout/` - Log out the user  
- **GET** `/users/profile/` - View and update user profile  
- **GET** `/users/dashboard/` - View user dashboard  
- **GET** `/users/dashboard/owner/` - View bike owner dashboard  
- **POST** `/users/bike-owner-request/` - Request bike owner verification  

------------------------------------------------------------------------------------------------------------------------

# Screenshots 🌟

![img.png](img.png)
![img_1.png](img_1.png)
![img_2.png](img_2.png)
![img_3.png](img_3.png)
![img_4.png](img_4.png)
![img_5.png](img_5.png)
![img_6.png](img_6.png)
![img_7.png](img_7.png)
![img_8.png](img_8.png)
![img_9.png](img_9.png)
![img_10.png](img_10.png)
------------------------------------------------------------------------------------------------------------------------

# Contributing 🤝
    Contributions are welcome! If you'd like to contribute to the project:

        -Fork the repository.
        -Create a new branch: git checkout -b feature-name.
        -Make your changes and commit them: git commit -m 'Add some feature'.
        -Push to the branch: git push origin feature-name.
        -Submit a pull request.

------------------------------------------------------------------------------------------------------------------------

# Contact 📬
    For any questions, feel free to reach out:

    ## Project Owner: Sudip Parajuli

    Email: sparajuli802@gmail.com
    GitHub: https://github.com/sudip-parajuli
    LinkedIn: https://www.linkedin.com/in/sudip-parajuli-8073601a1/
    Twitter (X): https://x.com/sudip_parajuli

------------------------------------------------------------------------------------------------------------------------

# Acknowledgments 🌟

    Shout out to:

        - Django and DRF community!
        

------------------------------------------------------------------------------------------------------------------------
