# Security and repository hygiene

## Files kept outside Git

Ignore rules exclude `.env` and environment variants, virtual environments, private keys, uploads at any `media/` directory, generated `staticfiles/`, database exports, caches, logs, old screenshots, diagnostic output, mobile build artifacts, and one-off root maintenance scripts. Public source assets and dependency lockfiles remain tracked.

The cleanup removes already-tracked uploads and local artifacts from the Git index. Files remain on the local disk. `.gitignore` alone never removes an already-tracked file. Back up uploads and databases outside the repository; a clean clone will not contain them.

Docker build exclusions also prevent environment files, private media, dependency caches and local artifacts from entering image layers.

## Secret management

- Use `.env.example` only as a template. Put real values in an ignored local `.env` or the hosting provider's secret store.
- Django's production signing key and Cloudinary credentials are required from configuration. SMTP, database and merchant passwords must not be embedded in source.
- Docker Compose requires a local database password and signing key through environment substitution.
- Keep server credentials out of the Expo application. Anything shipped to a client must be treated as public.
- Do not print credentials, signed payment payloads or tokens in logs. Do not paste them into issues, documentation or screenshots.

## Before committing and pushing

```powershell
git status --short
git diff --cached --stat
git ls-files -ci --exclude-standard
python scripts/check_secrets.py --staged
git diff --cached --check
```

The ignored-but-tracked listing should be empty. The checker inspects the entire staged index and reports only filenames, line numbers, and finding types, withholding suspected values. It catches common credential literals, provider tokens, private-key blocks, database credentials and tracked private/generated directories. It is intentionally limited: binary contents, unusual secret formats, historical commits and secrets in screenshots need a separate audit. Use a maintained secret-scanning service for ongoing protection.

## Previously published credentials or private data

Removal from the current branch does not erase Git history, forks, clones, cached pages or existing container images. Rotate any previously published application signing keys, SMTP passwords, cloud keys, merchant secrets and reused development passwords. Review uploaded identity documents and customer data already published in old revisions.

History cleanup needs a coordinated plan and backups. It changes commit IDs, may require a force push, and affects collaborators. This cleanup does not rewrite history or force-push. Follow the provider's incident process and rotate credentials before deciding on history removal.

## Payment protections and limits

PayPal return parameters cannot confirm a booking; a verified IPN must match the saved amount, currency, receiver and gateway mode. eSewa callbacks require signed details and matching saved transaction identifiers, amounts and merchant product codes. Online gateway initiation charges the saved payment amount and requires the booking owner. Completed payments cannot be downgraded by cancellation redirects.

Additional work remains around concurrent booking confirmation, partial deposits, private host documents, framework upgrades, and mobile token handling. See [the review](../PROJECT_REVIEW.md). These documents describe the implemented safeguards, not a security certification.
