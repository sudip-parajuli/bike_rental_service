# EasyMoto Operations

Staff workspace for Android, iPhone and the web, built with Expo SDK 54 / React Native and the existing Django API.

## What staff can do

- See overdue bikes, today's returns, upcoming pickups and pending reservations.
- Search and paginate rentals; open a customer or vehicle record.
- Edit pickup/return dates in **Nepal time**. Conflicting reservations and stale edits from another phone are rejected.
- Keep the agreed price, or explicitly recalculate it for an extension while preserving payments already received.
- Record a **physical return**, outstanding rental balance, security deposit and deposit handover separately.
- Open a customer WhatsApp reminder with their bike, rental number and exact return deadline. Staff review and send it.
- Enable phone reminders and optional server push; use automatic customer emails when configured.
- Download invoices and agreements using authenticated requests, without putting login tokens in URLs.

## Run

```sh
npm ci
cp .env.example .env
npm start
```

The default backend is `https://www.easymoto.com.np/api/mobile`. Set `EXPO_PUBLIC_API_URL` before starting/building to use another **trusted** backend. On a physical device, localhost is the phone itself: use a reachable development address. The backend must include this release's migrations and new staff routes. An old deployment will not support the new screens.

Sign in with an active staff/administrator username or email. Website customer accounts cannot enter this workspace. Native tokens are kept in Expo SecureStore; browser sessions use sessionStorage. Expired access tokens refresh once, concurrently queued requests share that refresh, and network failures do not erase the session.

## Verify

```sh
npm run typecheck
npm run lint
npm test
npx expo install --check
npx expo export --platform all
```

The nine client tests cover Nepal date/time boundaries, invalid calendar dates, concurrent token refresh, rejected credentials and offline refresh. Backend rental/reminder tests run from the repository root:

```sh
python manage.py test mobile_api bikes bookings payment chatbot --settings=bike_rental_service.settings.local --noinput
```

## Installable builds

```sh
npx eas-cli login
npx eas-cli build --platform android --profile preview
npx eas-cli build --platform ios --profile preview
```

Use your existing Expo project and signing credentials. The existing Android package is preserved. The iOS bundle identifier is `com.easymoto.operations`; if there is an existing distributed iOS app, use its identifier before building. A development/internal build is needed to test remote push; Expo Go is not a replacement for native delivery testing. Current iOS Expo Go versions might not support SDK 54.

Android push needs the Firebase Android app's `google-services.json` as an EAS **file** environment variable named `GOOGLE_SERVICES_JSON`, plus FCM v1 credentials configured for this Expo project. iPhone push needs APNs/signing credentials. Do not commit service-account files or signing keys. EAS free build allowances and Apple distribution requirements are account-dependent; no paid build or store submission is started by this repository.

The web export can be hosted as a staff portal for browser access, including iPhone, without publishing to an app store. Web mode provides the return queue and WhatsApp drafts; native phone notifications require the installed app.

## Notifications and release

See [the mobile operations release guide](../docs/MOBILE_OPERATIONS.md) for Render migrations, the free-oriented reminder scheduler, Firebase/APNs setup, delivery limitations and the device acceptance checks. Keep `.env`, `google-services.json`, `GoogleService-Info.plist`, generated builds and signing credentials outside Git.
