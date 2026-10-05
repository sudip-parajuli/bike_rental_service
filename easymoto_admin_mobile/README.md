# EasyMoto staff mobile app

This Expo / React Native application connects to the Django staff API for inventory, customers, bookings, maintenance and rental documents. It is separate from the public rental website.

## Run locally

```powershell
cd easymoto_admin_mobile
npm ci
npm start
```

Use the available `npm run android`, `npm run ios`, or `npm run web` scripts for your development target. `npm run lint` runs Expo's lint checks. Keep `package-lock.json` committed; ignore `node_modules/`, `.expo/`, generated builds, and signing credentials.

## Backend connection

API configuration is in `api/index.ts`. A web app running on `localhost` selects `http://localhost:8000/api/mobile`; other platforms currently select `https://www.easymoto.com.np/api/mobile`. A physical phone cannot reach your development computer through `localhost`. For local device development, deliberately configure your computer's reachable LAN address and the Django allowed hosts.

Login uses `POST /api/mobile/auth/login/` with a username or email and password. Only active staff/admin accounts may use the app. The client stores access tokens and attaches a Bearer authorization header to requests. Never embed the Django secret key, database credentials, cloud secrets, SMTP passwords, or merchant keys in the app.

## Build profiles

`eas.json` defines development, preview and production profiles. Review the actual file before selecting a profile. Configure Expo/EAS credentials through its credential tooling, not committed key files. Build output (`.apk`, `.aab`, `.ipa`) and signing material are ignored.

## Related documentation

- [Backend development](../docs/DEVELOPMENT.md)
- [Staff API routes](../docs/API.md)
- [Security and repository hygiene](../docs/SECURITY.md)
- [Known production limitations](../PROJECT_REVIEW.md)

The storefront regression suite does not test the native app. Verify mobile login, the selected backend, staff permissions, and document access separately before releasing a build.
