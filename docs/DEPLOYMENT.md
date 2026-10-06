# Deployment and media recovery

EasyMoto is hosted on Render, as confirmed by the project owner. The project contains Django/Gunicorn, Docker and Procfile deployment support. PostgreSQL is supplied by Neon. Verify the connected Git branch, domain, and deployment command in the Render service before release. A Git push may trigger an automatic deployment when the connected branch is configured that way.

## Production configuration

Set values in the hosting provider's environment settings; do not commit `.env`.

| Variable | Purpose |
| --- | --- |
| `DJANGO_ENV=production` | Select production settings |
| `SECRET_KEY` | Required unique Django signing key |
| `DATABASE_URL` | Required PostgreSQL connection string from Neon, including its SSL parameters |
| `ALLOWED_HOSTS` | Comma-separated domain names, such as `easymoto.com.np,www.easymoto.com.np` |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Required persistent image storage credentials |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP delivery |
| `PAYPAL_RECEIVER_EMAIL`, `PAYPAL_TEST` | PayPal merchant and sandbox/live mode |
| `ESEWA_PRODUCT_CODE`, `ESEWA_SECRET_KEY`, `ESEWA_GATEWAY_URL`, `ESEWA_VERIFY_URL` | Merchant signing key and environment-specific gateway URLs |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `PRODUCTION_DOMAIN` | Optional Google application synchronization at startup |
| `GEMINI_API_KEY` | Optional chatbot access |

Production startup fails when the application signing key or complete Cloudinary configuration is missing. Keep secure cookies and HTTPS redirects enabled behind the trusted HTTPS proxy. Review CSRF trusted origins when adding domains or hosting providers. Restrict CORS to approved clients before launch.

## Release sequence

1. Back up PostgreSQL and uploaded media separately. Confirm the intended release branch.
2. Install `requirements.txt` in the deployment environment.
3. Run `python manage.py collectstatic --noinput` with the intended production environment. The Dockerfile collects assets using local settings at image build time, avoiding production secrets in build layers.
4. Run `python manage.py migrate --noinput` against the intended database once per release.
5. Start `gunicorn bike_rental_service.wsgi:application`. For a custom container command, bind the interface and port required by the provider.
6. Confirm the public homepage, fleet, a bike photo, staff login, and sandbox payment notifications. Verify request scheme handling and generated HTTPS gateway URLs.

The supplied Procfile also runs `create_superuser_from_env`. That command can update an existing account's password from `DJANGO_SUPERUSER_PASSWORD`; use it only intentionally and keep those values private. Prefer an explicit one-time administrative setup rather than resetting credentials on every restart.

## Static assets versus uploads

- Source CSS, JavaScript, logos and application assets live in source-controlled static directories.
- WhiteNoise serves generated, hashed files in `STATIC_ROOT` after `collectstatic`.
- Uploaded bike photos use Cloudinary in production through `STORAGES['default']`.
- Neon stores image references and business records, not the photo bytes.
- Host ID, insurance and registration documents need private persistent storage with authenticated downloads. Their current explicit local storage is still an unresolved production issue; do not move them to a public CDN.

Django 5.1 removed the old `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` options. The updated configuration uses `STORAGES`. Changing the storage backend does not upload old local files or repair references to missing bytes.

## Recovering missing images

1. Inspect hosting logs and verify the Neon project and branch remain available. Do not run database reset or sample-data scripts.
2. Confirm all three Cloudinary variables are set for the production deployment.
3. Open an affected image URL. If bike records load but the image URL fails, investigate media storage independently of Neon.
4. Back up the database and original images before editing references. Local media copies are ignored by Git and must be preserved separately.
5. Locate the original photo and verify it matches the listed vehicle. Upload it through the admin editor, or enter a stable direct HTTPS image URL in Image URL. The external URL takes priority; clear it to use the upload again.
6. Repeat only after confirming each corrected image. Missing files that existed solely on ephemeral hosting storage require a backup or a new photo.

`/ping/` reports application liveness; it does not establish database or media health. Add separate database and image monitoring.

## Launch limitations

See [the project review](../PROJECT_REVIEW.md) for unsupported Django version, fixed PayPal exchange rate, partial-payment behavior, rental-day definition, concurrent booking confirmation, private documents, and remaining security work. Local tests and a successful static build do not validate live merchant settings.


## Render release for the storefront update

Run migration `bikes.0005_bike_image_url` before serving the new application: `python manage.py migrate --noinput`. It adds an optional URL field and makes uploads optional; it does not modify existing photo references. Deploy static assets with `collectstatic`. Configure `SITE_URL=https://www.easymoto.com.np` to generate canonical URLs and the sitemap. Run the migration in a pre-deploy step when your Render plan supports it, or in the release/start sequence before Gunicorn accepts traffic.

Google reviews are optional. In Render's private environment settings configure `GOOGLE_PLACES_API_KEY` and `GOOGLE_PLACE_ID`; enable Places API (New) and billing in the Google Cloud project. Restrict the key to the required API and apply quotas/budget alerts. Never put the key in HTML, Git, mobile client configuration or a `NEXT_PUBLIC`/`EXPO_PUBLIC` variable. See [STOREFRONT.md](STOREFRONT.md).

Render's ephemeral filesystem is unsuitable for durable uploads. Neon keeps database references, while Cloudinary or the external image provider serves the image bytes. A missing image alone does not prove that the database expired. External links also fail if providers block hotlinking or remove files. This release does not move existing uploads or verify the live Render deployment.
