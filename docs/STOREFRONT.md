# Storefront design and operations

## Design direction

The storefront uses EasyMoto's existing blue identity, bold editorial typography, open spacing, a dimensional Nepal riding illustration, soft depth motion and clean vehicle cards. The illustration is campaign artwork, clearly labelled; it does not represent the actual inventory or claim a specific route. Real bike cards use admin-selected photographs. Motion supports `prefers-reduced-motion`; touch devices do not get pointer tilt. Native FAQ disclosures work without JavaScript; the optional search filters questions and answers.

Research: [Twisted Road](https://www.twistedroad.com/) and [Riders Share](https://www.riders-share.com/) informed the emphasis on vehicle choice, trip planning, clear rental guidance and customer experience. The site uses lightweight CSS depth effects rather than a downloadable 3D model or a WebGL engine.

The generated campaign asset is `bike_rental_service/static/images/nepal-ride-3d.webp` (about 326 KB). The original PNG is kept locally and ignored. Generation prompt: "Use case: stylized-concept. Asset type: landscape website hero illustration for EasyMoto motorcycle rentals in Kathmandu, Nepal. Create a premium cinematic 3D editorial illustration: a single vivid electric-blue classic road motorcycle in three-quarter side view, on an elegant winding asphalt road through layered Himalayan foothills, distant snow peaks and softly hazy sky. Polished realistic 3D materials, tasteful soft sunlight, gentle blue reflections, sophisticated automotive campaign art. Composition: wide landscape 3:2, motorcycle prominent in right half, attractive layered road curves, pale cool sky and mountain tones with cobalt blue focal point, scene can be cropped on mobile. This is an explicitly illustrative campaign asset, not a photograph of real business inventory. No riders, no logos, no brand names, no text, no watermark, no fake reviews, no oversaturated neon. Render highly refined, visually striking, realistic bike geometry and wheels, generous breathing room around bike."

## External bike image URLs

1. Open a bike in Django admin (`/admin/`) or the staff bike editor (`/admin-panel/`).
2. Enter a **direct HTTPS image URL** in **Image URL**. An upload is optional. The URL takes priority over the upload; clear it to use the uploaded image again.
3. Save, then open the public fleet and bike detail page to verify the photograph.

Google Images is a discovery tool: a search-page URL is not an image URL. Open the original image source and use a stable direct file URL only when you have permission to display it. Prefer your own CDN, manufacturer-approved media or a provider that explicitly permits hotlinking. Temporary Google thumbnail URLs, expiring signed URLs and sites that block hotlinking are unreliable. Do not put credentials or private document links in the field. External files are displayed by the visitor's browser; the Django server does not download them or store their bytes. Missing images show a contact placeholder in fleet cards. Mobile API responses also resolve the chosen URL; image editing is provided in the web admin.

Migration: `python manage.py migrate --noinput` adds the optional field. Existing upload paths are preserved. External image selection does not delete existing uploaded files and does not solve an unreachable database.

## Business information

Document requirements come from the owner's supplied required-documents poster, plus their explicit IDP instruction. Deposit, return-time, helmet and fuel details come from the owner's confirmation:

- Usual deposit NPR 5,000; exact amount varies by vehicle and rental duration.
- Daily rentals only. The rental day ends at 7 PM.
- NPR 500 night or late-return charge after the deadline.
- Helmet provided; fuel paid for by the renter.

The FAQ source is `bike_rental_service/rental_content.py`. The chatbot reads the same FAQ source. The visible checklist and terms page must also be updated when policies change. Deposit collection and late-return charges are informational here; the existing booking/payment calculations do not automatically enforce these policies. Confirm the quote with the team, and reconcile billing rules before enabling automatic penalty calculations.

Location, phones and email were checked against the [Linkypot profile](https://easymoto.linkypot.com/), the supplied poster and the [Google business profile](https://share.google/iGOVRN5QGg3pxlHIp). Google listed Sun–Fri 7 AM–6:30 PM and Sat 8:30 AM–4 PM when checked on 2026-10-06; pickup appointments and holiday hours need confirmation. Cancellation, insurance, damage liability and deposit refund conditions remain unconfirmed, so the website directs riders to ask instead of inventing policies.

## Live Google reviews

The site offers the Google profile link immediately. Embedded reviews require private Render configuration:

- Enable **Places API (New)** in a Google Cloud project with billing enabled.
- Obtain the business **Place ID** using Google's official Place ID tooling. The `share.google` URL and a Maps CID are not Place IDs.
- Set `GOOGLE_PLACES_API_KEY` and `GOOGLE_PLACE_ID` in Render. Restrict the key to Places API and apply billing quotas and budget alerts. Keep it out of client code and Git.

`GET /api/reviews/google/` requests Place Details with a narrow field mask, a four-second timeout, and a five-requests-per-minute throttle per user/IP. It returns up to five Google-selected relevant reviews, not the full review history. It keeps author name/photo/profile link, original review text where available, source review link, date and provider attributions. Content is rendered with `textContent`, never HTML. Responses use `Cache-Control: no-store`; review payloads are not persisted. The homepage loads them when the reviews section approaches the viewport. Missing credentials, quota errors or outages leave the profile link visible. Production abuse protection should include an edge rate limit and API quota; in-process throttling alone is not a billing guarantee.

The Google Maps attribution image is an unmodified official asset from [Google's attribution package](https://developers.google.com/static/maps/documentation/images/Google_Maps_Attribution_Assets.zip), displayed with the required clear space and height. Review rendering follows [Places API policies](https://developers.google.com/maps/documentation/places/web-service/policies). Public terms and privacy pages link Google's applicable policies. Real credential-based access must be checked after configuring Render; automated tests use mocked responses.

## Search and AI discoverability

The homepage contains server-rendered business information and FAQs, canonical metadata, social preview metadata, LocalBusiness and matching FAQPage JSON-LD. `/sitemap.xml` includes approved bike detail pages; `/robots.txt` points to it and excludes account/admin/API areas. Set `SITE_URL` to the public HTTPS origin. Private pages receive `noindex` metadata; this is indexing guidance and does not replace authentication.

Structured data does not promise rankings or rich results. [Google's AI search guidance](https://developers.google.com/search/docs/appearance/ai-features) emphasizes the same crawlable, useful content as ordinary search. [FAQ rich results](https://developers.google.com/search/blog/2023/08/howto-faq-changes) are largely limited to authoritative health/government sites. Google ratings are not copied into self-serving LocalBusiness review markup.

## Verification

Run Django tests for bikes and payment, migration drift checks, a production-style static asset collection and `scripts/check_secrets.py --staged` before pushing. Browser-check desktop and mobile widths, the navigation, fleet image behavior, FAQ search and contact links. Local previews must use isolated fixtures rather than changing real customer/booking data.
Current release choice: the owner requested the Google profile link only. Leave the optional Places credentials unset; the homepage then makes no embedded-review request. No Google reviews have been copied into the local testimonials database.

## Fleet carousel, navigation and dated enquiries

A visible swipe hint and directional icon introduce the fleet carousel. Its scrollbar is hidden while touch scrolling, arrow controls and keyboard navigation remain available.

The homepage fleet is a single-row, centered carousel with a subtle dimensional treatment, previous/next buttons, a current-bike indicator, native touch/trackpad scrolling, and Arrow/Home/End keyboard support when the track is focused. The full searchable catalogue remains a grid. There is no autoplay. First/last slide spacing lets every bike reach the center. Images and card links remain readable and usable without JavaScript.

The hero no longer uses the generic location eyebrow with a dot. Its readable heading reveals three lines with staggered CSS animation. Desktop navigation starts at the top and becomes a floating bottom dock after scrolling more than 160px; returning to the top restores it. A reserved header space prevents layout shifts. At widths below 992px it remains a collapsible top navigation and leaves the chatbot at the bottom. Reduced-motion preferences disable the animation and dimensional movement. No GSAP dependency is required for these effects.

Fleet and bike-detail **Check dates** links open an accessible native dialog. Customers select pickup and return dates, prepare the enquiry, then open WhatsApp to review and send it. The draft includes the vehicle/fleet ID, both dates, the 7 PM Nepal-time return deadline, and a request to confirm availability and the total cost. This flow does not send messages automatically, create bookings or claim availability.

Without JavaScript or native dialog support, the links go to `/availability/?bike=<id>`. Server-side validation also rejects missing, malformed, past or reversed dates and non-public bikes; same-day daily rentals are valid. The current Nepal date is computed explicitly, independently of the server's timezone. Enquiry pages have `noindex` metadata.

Facebook, Instagram, Google and WhatsApp links use Font Awesome brand glyphs. The Linkypot logo is the unmodified PNG supplied by the project owner, stored as `bike_rental_service/static/images/linkypot.png`. The supplied ICO is not needed for this inline brand icon. Sample preview bike photos and all screenshots remain in ignored verification folders and are not deployment data.
