# Development

## Requirements and installation

Use a fresh Python 3.11/3.12 virtual environment and PostgreSQL. Do not reuse another computer's `.venv`; its interpreter paths and compiled packages may be incompatible. The requirements file is the dependency source of truth. Django is currently pinned to 5.1.6 and needs a separately tested supported-version upgrade.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Save the generated key privately as `SECRET_KEY` in `.env`. Populate `DB_*` for an existing local PostgreSQL database. Leave `DJANGO_ENV=local`; the local email backend writes mail to the console. Cloudinary is required for production uploads, but local bike uploads use `media/`.

```powershell
python manage.py migrate --settings=bike_rental_service.settings.local
python manage.py createsuperuser --settings=bike_rental_service.settings.local
python manage.py runserver --settings=bike_rental_service.settings.local
```

Use `/admin/` to add approved inventory. No private uploads, customer data, demo accounts, or fixed-password reset scripts are distributed. Use `python manage.py changepassword <username>` for a local password change.

## Docker development

Set `SECRET_KEY` and `DB_PASSWORD` in the root `.env`, then:

```powershell
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

The Compose stack is for local development. Django connects to the `db` service through `DB_HOST=db`; the database password is required from the local environment. PostgreSQL data stays in the named `postgres_data` volume. Do not delete that volume without a backup. This stack does not replace production media storage or production infrastructure.

## Google sign-in

Create a Google OAuth application with the appropriate callback URL, normally `http://127.0.0.1:8000/accounts/google/login/callback/` locally. In Django admin, set the Site domain and configure a Google Social Application linked to that Site. Store client credentials privately. Local startup can synchronize the Site using `PRODUCTION_DOMAIN`; set it to `127.0.0.1:8000` locally. Avoid configuring duplicate Google applications in both settings and the database.

## Checks

```powershell
python manage.py check --settings=bike_rental_service.settings.local
python manage.py test bikes payment --settings=bike_rental_service.settings.local --noinput
python scripts/check_secrets.py
python scripts/check_secrets.py --staged
git diff --check
```

The 18 targeted regression tests cover storefront rendering/fallback, approved reviews, filtering/pagination, public API privacy, media URLs, partially paid booking overlap, payment ownership, and payment callbacks. They use in-memory SQLite and dummy gateway values. They do not verify production credentials, PostgreSQL concurrency, or browser appearance.

Local static files use Django's development storage. Production uses WhiteNoise's manifest storage and must run `collectstatic` during build/deployment. New public assets belong in `bike_rental_service/static/`, not generated `staticfiles/`.

## Project layout

| Directory | Responsibility |
| --- | --- |
| `bike_rental_service/` | Settings, root routes, homepage, shared templates and static assets |
| `bikes/` | Inventory, host listings, public fleet and recommendations |
| `bookings/` | Rental dates, pricing, booking state and approval |
| `payment/` | Payments, invoices, PayPal and eSewa callbacks |
| `users/` | Accounts, host onboarding, contact and authentication |
| `testimonials/` | Reviews and approval |
| `admin_panel/` | Staff portal, contracts and administrative workflows |
| `mobile_api/` | Staff JWT authentication and mobile endpoints |
| `chatbot/` | Gemini integration and fleet lookups |
| `easymoto_admin_mobile/` | Expo staff application |
| `docs/`, `scripts/` | Maintainer guides and repository checks |

Commit migration files and dependency lockfiles. Ignore generated assets and private local data. See [security](SECURITY.md) before staging changes and [deployment](DEPLOYMENT.md) before publishing.
