# API reference

Routes are defined in each application's `urls.py`. JSON endpoints use Django REST Framework; some endpoints shared with HTML routes negotiate their response by path or the `Accept` header. Send `Accept: application/json` for API requests and use `Content-Type: application/json` for JSON payloads.

## Authentication

Customer endpoints support configured session, basic, and JWT authentication. Existing `/api/auth/` routes are provided by dj-rest-auth; use their actual configured login response rather than assuming the response contains a JWT. Session-authenticated modifying requests require CSRF protection.

Staff mobile clients obtain JWTs from `POST /api/mobile/auth/login/` using `login` (username or email) and `password`. Refresh through `POST /api/mobile/auth/refresh/`. Send `Authorization: Bearer <access_token>` afterward. Only active staff/admin users can access staff tools.

## Main routes

| Route | Purpose and access |
| --- | --- |
| `GET /api/bike/` | Public approved fleet; paginated, searchable and filterable |
| `GET /api/bike/<id>/` | Public approved vehicle details |
| `POST /api/bike/create/` | Authenticated host listing submission; requires approval |
| `/api/bike/<id>/update/`, `/delete/` | Host owner or staff mutation |
| `GET /api/bike/recommendations/` | Public/individual recommendations |
| `GET /api/bike/<id>/similar/` | Similar bikes |
| `GET /api/booking/`, `/<id>/` | Signed-in customer's own bookings |
| `POST /api/booking/create/` | Create a booking with bike, dates, pickup and payment option |
| `/api/booking/<id>/payment-select/` | Owner's online payment selection; current view reads form fields |
| `/api/booking/<id>/approve/`, `/reject/`, `/complete/` | Host booking workflow; see view-specific permission rules |
| `GET /api/payment/` | Own payments; staff may list all |
| `POST /api/payment/` | Initiate payment for an owned booking |
| `GET /api/payment/<booking_id>/` | Read-only payment detail, looked up by booking ID |
| `GET /api/testimonial/` | Public approved reviews |
| `/api/user/` | User/account and contact routes; permissions vary by view |
| `POST /api/chatbot/chat/` | Optional chatbot; requires configured Gemini access |

Public fleet responses omit chassis numbers, engine numbers and internal owner/maintenance identifiers. API permission and pagination defaults live in `bike_rental_service/settings/base.py`. Do not interpret the fleet's `availability_status` flag as date-specific availability.

## Fleet query parameters

`search`, `name`, `brand`, `type`, `availability_status`, `is_featured`, and `page` are supported for the fleet list. Types include `scooter`, `motorcycle`, and `electric`. The public HTML fleet at `/bikes/` preserves query parameters when paginating.

## Payment gateway routes

The `payment` routes are mounted under `/api/payment/`; reverse URL resolution may choose that mounted prefix even when the caller starts from an HTML page.

| Method and path | Behavior |
| --- | --- |
| `GET /api/payment/paypal/<booking_id>/<amount>/` | Owned booking's PayPal form; saved payment amount overrides the URL amount |
| `GET /api/payment/esewa/<booking_id>/<amount>/` | Owned booking's signed eSewa form and stored payment attempt |
| `GET /api/payment/esewa-success/` | Signed gateway callback; requires matching payment details |
| `GET /api/payment/esewa-failure/` | Failure/cancellation display; completed payments remain completed |
| `GET /api/payment/paypal-return/` | Display completion/pending state; does not confirm a payment |
| `GET /api/payment/paypal-cancel/` | Cancellation display |
| `POST /api/payment/paypal-ipn/` | Verified PayPal IPN handling |

Booking payment states are `unpaid`, `partial`, and `paid`; do not submit booleans for them. Payment record states are separate (`pending`, `partial`, `completed`, `failed`). Partial deposits and the fixed PayPal conversion policy need further work as described in the review.

## Staff mobile tools

The `/api/mobile/` namespace includes dashboard statistics, bikes, maintenance, customers, walk-in bookings, marking bookings paid, invoice/contract exports and staff activity. See `mobile_api/urls.py` for the exact routes. Staff/admin access is required; customer tokens are insufficient.

## HTML entry points and generated documentation

`/`, `/public-home/`, `/bikes/`, `/users/login/`, `/users/register/`, `/users/dashboard/`, `/users/dashboard/host/`, `/bookings/`, `/admin/`, and `/admin-panel/` provide website interfaces. `/ping/` is a liveness endpoint.

Swagger and ReDoc are available at `/api/swagger/` and `/api/redoc/`. They describe DRF routes, but do not capture all template/form overrides. Verify a view's implementation before relying on generated method or request-body information.

## External images and Google review display

Bike creation/editing through the web staff forms and the bike model serializers accept optional `image_url` (direct HTTPS only, max 1,000 characters). The upload is optional. Public `image` and mobile `image_url` responses use the external URL first, then the uploaded file, and otherwise return an empty/null value. The mobile `image_url` is a computed display field; use the web editor to change the image source.

`GET /api/reviews/google/` is an optional public, throttled display endpoint. Unconfigured or failed upstream requests return `{"available": false}`. Configured responses include author and source attribution for up to five relevant Google Places reviews. The response is not cached. The current release uses only the Google profile link, per the owner's choice; credentials remain optional. Setup is documented in [STOREFRONT.md](STOREFRONT.md).

`/sitemap.xml`, `/robots.txt`, `/privacy/` and `/terms/` are public website resources.

`GET /availability/?bike=<approved-bike-id>` renders a public date enquiry form. Supplying valid `start` and `end` ISO dates (`YYYY-MM-DD`) returns a 302 redirect to WhatsApp with the prepared message; no booking or message is created. Same-day rentals are allowed, past pickup dates and returns before pickup are rejected. Non-public or invalid bike IDs return 404.
