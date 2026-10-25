# Mobile rental operations

## Release contents

This release keeps Expo / React Native and repairs the staff workflow instead of replacing the Django backend. It adds a return queue, editable rental dates, physical returns, deposits, customer reminder drafts, secure token storage, refresh rotation, authenticated PDF downloads and a reminder outbox.

The previous app discarded expired sessions, guessed the API host from the platform, loaded only the first results page, exposed bearer tokens in PDF URLs and had no booking-edit/return API. The old dashboard also excluded unpaid and overdue rentals. The new app uses explicit API configuration and a staff-only rental board that includes those rentals.

## Deployment order

1. Back up the production database and confirm the Render service/branch.
2. Deploy this backend and run `python manage.py migrate --noinput` before installing the new app. This creates the mobile operation/reminder tables and SimpleJWT blacklist tables. The existing Procfile already runs migrations; confirm Render uses it or add migrations to the deployment command. Existing agreed rental totals are not changed by the migration. The User model is also brought back into alignment with its already-existing licence/passport columns; no identity data is dropped.
3. Verify staff sign-in, `GET /api/mobile/me/` and `GET /api/mobile/rental-board/` using a staff account. Customer and anonymous access must be rejected.
4. Build/install the updated app for the intended backend. See [mobile README](../easymoto_admin_mobile/README.md).
5. Configure reminders below, then run the device acceptance checks.

Do not reuse old PDF links containing `?token=`; the backend now rejects query-string bearer authentication. Native downloads keep authorization in headers and delete temporary PDFs after the share sheet finishes.

Render's [free web services](https://render.com/docs/free) can take about a minute to wake from idle. The mobile client allows a 75-second first connection, shows a connecting message and preserves tokens on network errors.

## Rental rules and accounting

All edited dates and displayed deadlines use Asia/Kathmandu, independently of the phone/server timezone. The new walk-in screen defaults return to **7 PM**. Daily pricing counts inclusive Nepal calendar dates, including a one-day rental when pickup and return fall on the same date.

A confirmed reservation blocks its interval even when unpaid. Staff creation and date updates lock the vehicle, check for conflicts and require a current `updated_at` version for edits. The lock guarantee covers these mobile write paths; other legacy website/payment flows still need their own concurrent-booking review.

An overdue confirmed rental stays on the road until staff explicitly record the physical return. A vehicle with an unresolved overdue rental cannot be assigned again through the mobile app. Completing a return does not mark it paid or return its deposit automatically. Recording payment afterwards does not reopen the rental.

Changing dates preserves the agreed price by default. Staff can choose to recalculate the duration-based total, using the contract's saved daily rate/manual discount where available. The cash already received is retained; increased totals become an outstanding balance. Any overpayment/refund must be reconciled by the team. Security deposits are recorded separately from rental income. NPR 500 late/night charges are informational and are not automatically posted or collected.

Returned rental dates/prices are locked, but staff can add handover notes and confirm the deposit was returned later. Changes are audited. Newly added walk-in customer records have unusable passwords rather than emailing plaintext credentials.

## Free-oriented reminders

### In-app and local phone reminders

The return queue works without any notification provider. Staff can enable reminders on their phone. With permission, the app schedules the next 20 upcoming returns (up to 60 local alerts) at 24 hours before, 3 hours before and at the return deadline. It refreshes those schedules when reopened and after edits made on that phone.

Local schedules cannot learn about another staff member's date changes while the app is closed. Server push is the appropriate mode for that case. When push registration succeeds and server reminders are enabled, the app cancels its local schedules to avoid duplicate alerts.

### Server staff push

[Expo's push service has no per-message charge](https://docs.expo.dev/push-notifications/faq/). Native delivery still requires a built app, device permission, and platform credentials. Follow the [official Expo setup](https://docs.expo.dev/push-notifications/push-notifications-setup/).

- Android: register the existing Android application ID in Firebase, provide its Google services JSON through the EAS file variable `GOOGLE_SERVICES_JSON`, and configure FCM v1 credentials in the Expo project.
- iPhone: configure APNs and signing for `com.easymoto.operations` (or the actual existing app identifier). Apple distribution normally requires its [Developer Program](https://developer.apple.com/programs/whats-included/); do not assume native iPhone distribution is entirely free. Browser access remains an alternative.
- Enable reminders inside each staff member's installed app. The device registers against their authenticated account. Notifications go to active staff/administrator devices, not customer accounts.
- Lock-screen alerts contain a rental number/deadline, not customer names, phone numbers or identity documents. Tapping opens the protected rental screen.
- If Expo enhanced push security is enabled, set the server-only `EXPO_ACCESS_TOKEN` in Render. Never use an EXPO_PUBLIC variable for this token.

### Automatic customer email

This is optional and uses the existing SMTP configuration. Set `RENTAL_EMAIL_REMINDERS_ENABLED=true` only when the mailbox/provider is configured and these transactional reminders are appropriate for your customers. No new paid email service is introduced; its existing quotas/billing still apply. Missing and placeholder customer emails are skipped.

### Customer WhatsApp

The app prepares a message for the customer's number with the actual saved return deadline, in Nepal time. Nepal 10-digit mobile numbers are normalized to country code 977; international numbers need their country code. Staff review and send the message in WhatsApp.

No unofficial WhatsApp automation or paid Business API is installed. Opening a draft is audited as **prepared**, never as delivered. This is intentionally different from automatic email/staff push.

### Scheduler on the existing service

Render settings:

```text
RENTAL_REMINDERS_ENABLED=true
RENTAL_EMAIL_REMINDERS_ENABLED=false
RENTAL_CRON_SECRET=<at least 32 random characters, stored privately>
EXPO_ACCESS_TOKEN=<only if Expo enhanced push security is enabled>
```

Generate the cron secret privately; do not paste it into chat or commit it. To preview without sending:

```sh
python manage.py dispatch_rental_reminders
```

An existing server scheduler can run `python manage.py dispatch_rental_reminders --send` every 15 minutes. Do not add an always-on paid worker just for this small queue.

Alternatively, the included GitHub Actions workflow uses a standard hosted runner within the repository's plan allowance. Set:

- Repository secret `RENTAL_CRON_SECRET`: the same value as Render.
- Repository variable `RENTAL_REMINDERS_ENABLED`: `true` only after delivery is configured.

The workflow posts only to `https://www.easymoto.com.np/api/mobile/reminders/run/`. It refuses redirects and never puts the credential in a URL. The job stays disabled when the repository variable is absent. No credentials or configuration are automatically uploaded by the code change.

This schedule is best effort: [GitHub scheduled runs may be delayed](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), and free hosting/phone power settings can delay delivery. Keep the in-app queue as the operational source of truth; do not promise exact-minute delivery on free infrastructure.

## Delivery behavior and monitoring

The outbox deduplicates each rental/due-date snapshot/reminder stage/recipient. It sends the current stage rather than replaying every missed stage. Date changes invalidate unsent old snapshots, and completed/cancelled/inactive rentals are skipped. Edits to notes do not cancel a valid pending reminder.

Push tickets are stored as **accepted**, then Expo receipts are checked on later runs. A sent/accepted receipt is not proof the person read the notification. Invalid devices are disabled. Known failures have a bounded retry/backoff; ambiguous timeouts and interrupted sends become **uncertain** rather than being automatically duplicated. No network delivery system guarantees exactly-once notification delivery.

Administrators can inspect staff devices, rental states and reminder delivery states/error codes in Django admin. Device tokens are hidden there. Inspect uncertain outcomes before any manual resend. No real customer messages are sent by the automated tests.

A phone signing out clears its local schedules and attempts device unregistration/token revocation. If it is offline, backend revocation cannot be confirmed until it reconnects; push contents stay generic. Run `python manage.py flushexpiredtokens` periodically to remove expired JWT blacklist records.

## Verification and remaining work

Automated checks cover guest/customer denial, staff/superuser access, date conflicts, optimistic locking, calendar-day pricing, keeping payments on extension, physical return, separate deposit handover, reminder invalidation/idempotency, safe WhatsApp drafts, JWT refresh/logout and secret-gated dispatch. Client tests cover Nepal date boundaries and token-refresh concurrency/offline behavior.

The native UI and push delivery must be tested on real Android and iPhone devices after signing credentials are configured. The desktop computer-use browser check was stopped because its policy layer could not verify the current browser URL; it did not establish a visual/device test result. JavaScript bundle export is not an APK/IPA or proof of delivery.

The dependency audit was improved with compatible patches, removing critical advisories present at the start. Some Expo SDK 54 transitive advisories remain (URL decoder, development image parsing and certificate tooling). A patched node-forge release was not available in the registry during this work; an incompatible image-size major override was removed after the native build caught it. Do not expose the Metro development server publicly or feed it untrusted build assets. Track the remaining audit report and test a supported Expo SDK upgrade separately.

## Phone acceptance checks

- Sign in by username and email; deny a customer account; background/reopen and test an expired access token.
- Create a same-day rental, record an advance and a separate deposit, and inspect both PDFs.
- Extend the return date, optionally recalculate the quote, and confirm another phone sees the new dates. A stale edit must request a refresh.
- Try a conflicting reservation and verify no extra booking/contract/payment was created.
- Let a rental become overdue; it must remain in the return queue until physically returned.
- Open a WhatsApp draft and verify recipient, bike and return deadline. Only the staff member sends it.
- In an installed build, allow notifications; test foreground, background, closed-app and a changed deadline.
- Configure the scheduler, verify Expo receipts and a test mailbox, then test duplicate runs, disabled devices and a cancelled/returned rental.
- Return a bike with money still outstanding, record payment later, and verify it stays returned.
