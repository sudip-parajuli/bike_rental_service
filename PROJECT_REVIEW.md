# EasyMoto project review and recovery guide

Reviewed on 5 October 2026. Scope: Django settings, public templates and scripts, bike/user models and serializers, booking validation, payment initiation and callbacks, admin access middleware, mobile API authentication, chatbot availability, migrations, and deployment files. The existing mobile app configuration change was preserved. This is a code review and local remediation, not an independent penetration test or a verification of the live hosting accounts.

## Assessment

The supplied design critique is substantially supported by the local code and live homepage: registration-first hero, overlapping JavaScript fleet, repeated benefits, empty reviews, and unsubstantiated operational claims. The public homepage exposes the existing phone number and Budhanilkantha location, which the revised storefront retains. Facebook, Instagram, Linkypot, and the remote GitHub repository could not be retrieved by the web tool; the local repository was used for code analysis. No social content or reviews were invented.

The project is a Django application with PostgreSQL, Cloudinary uploads, WhiteNoise static assets, customer and host workflows, a custom admin portal, a Gemini chatbot, and an Expo admin mobile app. Deployment files mention Render and Gunicorn/Docker; there is no application Vercel configuration in the supplied root. Confirm which deployment and branch actually serve the domain before publishing.

## Changes implemented

- Replaced the homepage with a responsive blue-and-white layout: location, browsing and WhatsApp actions, real inventory-derived starting price, three fleet cards, rental steps, terms checklist, approved reviews, pickup contact, and social links.
- Removed unverified counts, insurance promises, hourly plans, and round-the-clock support claims. Specific document, deposit, and cancellation rules must come from the business.
- Homepage and fleet cards now render on the server, without an API call or carousel dependency. The homepage preserves direct contact when database queries fail.
- Added honest photo-unavailable states, distinct fleet IDs/colors/model years, and date-checking language rather than unconditional availability promises.
- Replaced the fleet's client-side HTML interpolation with escaped Django templates. Search/type filters and pagination work without JavaScript; query parameters persist across pages.
- Updated Django storage configuration to STORAGES for both Cloudinary media and WhiteNoise static assets. Django 5.1 removed DEFAULT_FILE_STORAGE and STATICFILES_STORAGE; the previous settings could silently leave media on local disk.
- Production now requires a secret key and complete Cloudinary credentials instead of silently selecting ephemeral upload storage. Docker collects static assets with local build settings so production secrets are not needed in image build layers.
- Removed hardcoded SMTP and local database passwords from settings; documented environment variables.
- Removed Django's production local-media serving workaround. It does not make uploaded files persistent and can expose locally stored documents.
- Public bike APIs exclude chassis numbers, engine numbers, host IDs, and internal approval/maintenance data.
- PayPal browser redirects no longer mark payments completed. Verified IPNs must match amount, currency, recipient, gateway mode, and payment method. Generated gateway links use the request scheme.
- eSewa callbacks require signed transaction details, matching amount/product/payment attempt, and constant-time signature comparison. Gateway charges come from saved payment amounts, not URL parameters. Booking payment status remains a defined string value.
- Payment initiation requires the booking owner; list/detail APIs restrict records to their owner or staff. Customer payment records cannot be edited/deleted through the payment detail API. Cancellation cannot downgrade a completed payment.
- Partially paid bookings block overlapping dates in the serializer and chatbot availability lookup.

## Image diagnosis: Neon versus Cloudinary

Neon stores database records, including the image filename/public ID. Cloudinary stores photo bytes. A suspended database can explain inventory API errors, but missing photos while bike records still load also points to storage or missing files. The invalid Django storage settings are a concrete local defect; they do not prove the exact cause of the deployed outage.

Check in the real hosting account:

1. Verify the domain points to the intended deployment and Git branch.
2. Set DJANGO_ENV=production, SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS, CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET. Include both easymoto.com.np and www.easymoto.com.np in ALLOWED_HOSTS. Use the Neon dashboard's connection string and required SSL settings.
3. Confirm Neon project/branch exists and inspect deployment logs for connection failures. Do not reset or reseed the production database.
4. Inspect a bike image URL. Updated production media URLs should use HTTPS Cloudinary delivery. If the database currently holds a local filename for a photo never uploaded to Cloudinary, changing storage settings cannot recover its bytes.
5. Back up the database and original media. Re-upload affected photos using the existing admin bike editor and original files; confirm the new image resolves before replacing another record. Missing ephemeral files require an original backup or a new photo.
6. Run migrations and collectstatic in the deployment process. Confirm the homepage, fleet, one photo, login, admin, and sandbox payments before accepting live bookings.

## Remaining work before production launch

- Rotate the previously embedded SMTP password and default application secret if either was used in production. Removing them from current files does not remove Git history. Verify environment keys privately; never paste them into a report.
- Upgrade Django 5.1.6 to a currently supported release and update/test dependent authentication and payment packages. The current Django documentation marks 5.1 unsupported. This pass fixes storage compatibility but does not change the framework version.
- Confirm actual rental policies and replace the terms checklist with approved business details. Supply current original photos for missing media.
- PayPal still uses the existing fixed NPR-to-USD conversion of 135. Replace it with a business-approved, recorded quote policy before offering live PayPal charges.
- Partial-payment pricing is not consistently implemented: payment serializers currently charge the full booking total. Define deposit percentage/amount and balance settlement before advertising partial online payments. An eSewa verified attempt now binds to its stored amount, but this does not implement a deposit product.
- Booking confirmation needs transaction-safe overlap protection when concurrent payment callbacks confirm two pending reservations. Serializer checks alone cannot prevent this race. Handle conflicts/refunds explicitly before scaling instant booking.
- Rental duration currently uses elapsed whole days plus one, charging two days for exactly 24 hours. Confirm the business rental-day definition before changing existing contractual billing logic.
- Booking serializer partial updates assume all date fields are present; add dedicated update validation and locks for paid bookings before offering customer amendments.
- Host onboarding documents use explicit local filesystem storage in users/models.py; these require a private persistent storage solution and authenticated downloads. Do not publish ID/insurance documents to a public image CDN. Existing local files need a private migration plan.
- Restrict production CORS origins to actual website/mobile web clients. Review mobile query-string JWT downloads, debug payment logs, API documentation exposure, and Gemini dependency maintenance.
- Establish automated database/media backups and monitoring. /ping/ is application liveness only, not database or media health.

## Verification

Regression tests cover server-rendered fleet/reviews, homepage database outage contact, fleet filtering/pagination, public API privacy, WhiteNoise/Cloudinary storage selection, unsigned/wrong-amount eSewa callbacks, successful signed callbacks, forged PayPal return parameters, matching/mismatched IPNs, URL amount tampering, and cancellation after completion.

Run in a working project environment:

```powershell
python manage.py test bikes payment --settings=bike_rental_service.settings.local --noinput
python manage.py check --settings=bike_rental_service.settings.local
```

Tests use an in-memory SQLite database. They do not establish connectivity to Neon or Cloudinary, validate live payment credentials, or prove PostgreSQL concurrency behavior. The supplied Windows virtual environment points to an unavailable Python 3.11 executable; local verification used the bundled Python 3.12 runtime with isolated compatibility dependencies in ignored .test-deps.

Local verification result: 18 regression tests passed, Django system checks reported no issues, and WhiteNoise collectstatic generated hashed URLs for the new stylesheet and existing logo in an isolated .verification-static directory. Browser layout checks and live account connectivity were not performed.

The supplied media/bikes directory contains local photo files, including 2018-honda-dio.jpg, dio-green.jpg, classic350.jpg, and bullet_classic_reborn.jpg. These may help recovery; confirm each file belongs to the listed vehicle before re-uploading it. Do not bulk replace image database references without checking Cloudinary uploads and backing up the database.

## Repository and documentation cleanup

The README now links to dedicated development, deployment/media recovery, API and security guides. The staff app README describes its actual backend selection and staff login requirements. `.gitignore` and `.dockerignore` exclude private uploads, environment files, generated assets, build output and local diagnostics. Already-tracked local artifacts were removed from the index while preserving disk copies. A lightweight staged secret checker reports suspected values by location without printing them. Docker Compose no longer embeds its database password; settings no longer contain the former fixed development signing key or merchant signing-key default. This cleanup does not rewrite Git history, rotate live credentials, or change the existing local mobile build-profile edit.

## Sources

- Live homepage: https://www.easymoto.com.np/
- Django 5.1 release notes and removed storage settings: https://docs.djangoproject.com/en/5.1/releases/5.1/
- Cloudinary storage package: https://github.com/klis87/django-cloudinary-storage
