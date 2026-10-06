# EasyMoto Rental Services

EasyMoto is a scooter and motorcycle rental service based in Budhanilkantha, Kathmandu. This repository contains its Django website, customer and host workflows, administrative portal, and Expo staff app.

[Website](https://www.easymoto.com.np/) · [Facebook](https://www.facebook.com/Easymoto.np) · [Instagram](https://www.instagram.com/easymoto_np/) · [More links](https://easymoto.linkypot.com/)

## What the project includes

- Public fleet browsing with model search, type filters, daily rates, and pagination.
- A server-rendered homepage with featured vehicles, approved reviews, pickup information, and WhatsApp contact.
- Customer registration, Google sign-in, booking requests, and rental history.
- Host listing submissions and administrative approval.
- PayPal and eSewa integrations with verified payment callbacks.
- An admin portal for bikes, bookings, payments, contracts, and customer records.
- Staff mobile tools and an optional Gemini chatbot.

Daily prices are in NPR. Visitors can browse without an account; online booking requires sign-in. Contact the business to confirm dates, deposit, documents, and rental terms.

## Documentation

| Guide | Contents |
| --- | --- |
| [Development](docs/DEVELOPMENT.md) | Local installation, Docker development, checks, and project layout |
| [Deployment and media recovery](docs/DEPLOYMENT.md) | Production settings, Neon, Cloudinary, static assets, and missing photos |
| [API](docs/API.md) | Routes, authentication, access rules, and payment callbacks |
| [Security and repository hygiene](docs/SECURITY.md) | Secrets, ignored files, backups, and pre-push checks |
| [Project review](PROJECT_REVIEW.md) | Findings, implemented improvements, verification, and remaining work |
| [Staff mobile app](easymoto_admin_mobile/README.md) | Expo setup and backend configuration |

## Local quick start

Use Python 3.11 or 3.12 and a local PostgreSQL database. Run these commands from the repository root in PowerShell:

```powershell
git clone https://github.com/sudip-parajuli/bike_rental_service.git
cd bike_rental_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` privately. Set a unique `SECRET_KEY` and the local `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`. Create that database in PostgreSQL before continuing. Local settings use these `DB_*` values; `DATABASE_URL` is used by production settings.

```powershell
python manage.py migrate --settings=bike_rental_service.settings.local
python manage.py createsuperuser --settings=bike_rental_service.settings.local
python manage.py runserver --settings=bike_rental_service.settings.local
```

Open `http://127.0.0.1:8000/`. Add and approve actual vehicle listings in `/admin/`; mark selected listings featured to display them prominently. The repository does not contain customer uploads or a production database backup. See the development guide for Google sign-in and staff setup.

## Verification

```powershell
python manage.py check --settings=bike_rental_service.settings.local
python manage.py test bikes payment --settings=bike_rental_service.settings.local --noinput
python scripts/check_secrets.py --staged
```

The targeted suite currently has 18 regression tests. Tests use an in-memory SQLite database and do not connect to Neon or payment gateways. The secret checker is a lightweight safeguard, not a full historical secret audit.

## Production status

Production requires `DJANGO_ENV=production`, a strong `SECRET_KEY`, `DATABASE_URL`, explicit allowed hosts, and complete Cloudinary credentials. Uploaded media must be stored persistently; WhiteNoise serves collected static assets, not customer uploads.

Before enabling live payments, resolve the outstanding issues described in the review: the fixed PayPal conversion rate, partial-payment policy, concurrency during booking confirmation, and private host-document storage. Django is currently pinned to 5.1.6; plan and test an upgrade to a supported release. A successful local test run is not a production-readiness certification.

## Contributing

Keep source assets, migration files, and dependency lockfiles in Git. Keep environment files, uploads, database exports, generated assets, logs, and build output outside Git. Back up media and data separately. Use a feature branch for new work, run the checks above, and review the staged diff before pushing.

## Storefront and external photos

The public website now uses an original compressed campaign illustration, subtle pointer depth, floating artwork, scroll reveals, responsive fleet cards and searchable native FAQ disclosures. Motion is disabled for users who prefer reduced motion. Core fleet, business details, requirements and FAQ content render on the server and remain readable without JavaScript.

Admins can add a **direct HTTPS image URL** in the bike editor instead of uploading a file. It takes priority over the uploaded image and is returned consistently by public and mobile bike APIs. See [storefront operations](docs/STOREFRONT.md) for image guidance, business copy and live Google reviews setup. Hosting is **Render**, with PostgreSQL on **Neon**; uploaded bike photos continue to use Cloudinary.

The homepage publishes document checklists including IDP for international customers, the usual NPR 5,000 variable deposit, daily rentals with a 7 PM return deadline, NPR 500 night/late-return charge, provided helmets and renter-paid fuel. These are customer information; this update does not introduce automatic deposit collection or late-fee billing.

The homepage now presents its bikes in a compact carousel. Desktop navigation floats at the bottom, while mobile keeps a top menu. Availability enquiries collect pickup/return dates before preparing a WhatsApp draft, with a regular-page fallback and server-side date validation. See [storefront interaction details](docs/STOREFRONT.md#fleet-carousel-navigation-and-dated-enquiries).
