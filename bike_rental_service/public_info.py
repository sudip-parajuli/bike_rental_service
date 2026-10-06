import json
from urllib.parse import quote
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import escape
from .rental_content import FAQS
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.throttling import UserRateThrottle


class GoogleReviewThrottle(UserRateThrottle):
    scope = 'google_reviews'
    rate = '5/minute'



def seo_context(request):
    origin = settings.SITE_URL.rstrip('/')
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'LocalBusiness', 'name': 'EasyMoto Rental Services',
         'url': origin, 'telephone': '+9779860702780',
         'email': 'easymotoservices@gmail.com',
         'address': {'@type': 'PostalAddress', 'streetAddress': 'Budhanilkantha-03, opposite Park Village Resort',
                     'addressLocality': 'Kathmandu', 'addressCountry': 'NP'},
         'sameAs': ['https://www.facebook.com/Easymoto.np', 'https://www.instagram.com/easymoto_np/']},
        {'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}}
            for _, q, a in FAQS]},
    ]}
    path = '/' if request.path == '/public-home/' else request.path
    return {'canonical_url': origin + path,
            'google_reviews_enabled': bool(settings.GOOGLE_PLACES_API_KEY and settings.GOOGLE_PLACE_ID),
            'private_page': request.path.startswith(('/admin', '/users/', '/accounts/', '/bookings/', '/api/')),
            'storefront_schema': json.dumps(schema).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026'),
            'public_origin': origin}


@api_view(['GET'])
@throttle_classes([GoogleReviewThrottle])
@permission_classes([AllowAny])
def google_reviews(request):
    key, place = settings.GOOGLE_PLACES_API_KEY, settings.GOOGLE_PLACE_ID
    unavailable = {'available': False}
    if not key or not place:
        response = JsonResponse(unavailable)
    else:
        try:
            upstream = requests.get('https://places.googleapis.com/v1/places/' + quote(place, safe=''),
                headers={'X-Goog-Api-Key': key,
                         'X-Goog-FieldMask': 'rating,userRatingCount,reviews,googleMapsUri,attributions'}, timeout=4)
            upstream.raise_for_status()
            data = upstream.json()
            reviews = []
            for review in data.get('reviews', [])[:5]:
                author = review.get('authorAttribution', {})
                reviews.append({'rating': review.get('rating'), 'text': review.get('originalText', review.get('text', {})).get('text', ''),
                    'author': author.get('displayName', ''), 'author_url': author.get('uri', ''),
                    'photo': author.get('photoUri', ''), 'url': review.get('googleMapsUri', ''),
                    'time': review.get('relativePublishTimeDescription', '')})
            response = JsonResponse({'available': bool(reviews), 'rating': data.get('rating'),
                'count': data.get('userRatingCount'), 'reviews': reviews, 'url': data.get('googleMapsUri', ''),
                'attributions': [{'name': a.get('provider', ''), 'url': a.get('providerUri', '')}
                                 for a in data.get('attributions', [])]})
        except (requests.RequestException, ValueError, TypeError, AttributeError):
            response = JsonResponse(unavailable)
    response['Cache-Control'] = 'no-store'
    return response


def robots(request):
    return HttpResponse('User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /admin-panel/\nDisallow: /api/\nDisallow: /users/\nDisallow: /accounts/\nDisallow: /bookings/\nSitemap: ' + settings.SITE_URL.rstrip('/') + '/sitemap.xml\n', content_type='text/plain')


def sitemap(request):
    from bikes.models import Bike
    from django.db import DatabaseError
    paths = ['/', reverse('bikes:bike-list'), reverse('privacy'), reverse('terms')]
    try:
        paths += [reverse('bikes:bike-detail', args=[pk]) for pk in Bike.objects.filter(is_approved=True).values_list('pk', flat=True)]
    except DatabaseError:
        pass
    locations = ''.join('<url><loc>' + escape(settings.SITE_URL.rstrip('/') + p) + '</loc></url>' for p in paths)
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + locations + '</urlset>', content_type='application/xml')


def policy(request, kind):
    return render(request, 'rental_policy.html', {'policy_kind': kind})
