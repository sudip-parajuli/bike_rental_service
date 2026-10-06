from io import StringIO
from unittest.mock import Mock, patch

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from bikes.models import Bike
from .services import FALLBACK, get_chatbot_response, public_fleet


@override_settings(GEMINI_API_KEY='fake-provider-key', GEMINI_MODEL='gemini-3.5-flash-lite')
class ChatbotServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        host = get_user_model().objects.create_user(username='chat-host', phone_number='+9779800000009')
        cls.bike = Bike.objects.create(host=host, name='Public scooter', type='scooter', price_per_day=1500, is_approved=True)
        Bike.objects.create(host=host, name='Private motorcycle', type='motorcycle', price_per_day=2500)

    def provider_response(self, **candidate):
        return Mock(status_code=200, json=Mock(return_value={'candidates': [{
            'finishReason': 'STOP', 'content': {'parts': [{'text': 'Please confirm your route with our team.'}]}, **candidate,
        }]}))

    @patch('chatbot.services.requests.post')
    def test_short_rental_faqs_do_not_use_free_api_quota(self, post):
        for question, expected in [
            ('How much is the deposit?', '5,000'),
            ('What documents do international customers need?', 'International Driving Permit'),
            ('Do you provide a helmet?', 'Fuel is paid'),
            ('What is the return deadline?', '7 PM'),
            ('Where is your shop located?', 'Park Village'),
            ('What are your opening hours?', 'Saturday'),
        ]:
            with self.subTest(question=question):
                self.assertIn(expected, get_chatbot_response(question))
        post.assert_not_called()

    @patch('chatbot.services.requests.post')
    def test_complex_query_uses_configured_model_bounded_request_and_public_context(self, post):
        post.return_value = self.provider_response()
        result = get_chatbot_response('Which scooter suits my planned journey?')
        self.assertIn('confirm your route', result)
        args, kwargs = post.call_args
        self.assertTrue(args[0].endswith('/models/gemini-3.5-flash-lite:generateContent'))
        self.assertNotIn('fake-provider-key', args[0])
        self.assertEqual(kwargs['headers']['x-goog-api-key'], 'fake-provider-key')
        self.assertEqual(kwargs['timeout'], (3, 12))
        self.assertFalse(kwargs['allow_redirects'])
        payload = kwargs['json']
        self.assertEqual(payload['generationConfig']['maxOutputTokens'], 512)
        context = payload['systemInstruction']['parts'][0]['text']
        self.assertIn('Public scooter', context)
        self.assertNotIn('Private motorcycle', context)
        self.assertNotIn('chat-host', context)
        self.assertNotIn('phone_number', context)

    @override_settings(GEMINI_API_KEY='')
    @patch('chatbot.services.requests.post')
    def test_missing_key_keeps_faqs_working_and_other_queries_get_contact(self, post):
        self.assertIn('5,000', get_chatbot_response('Deposit amount?'))
        self.assertEqual(get_chatbot_response('Which scooter suits my planned journey?'), FALLBACK)
        post.assert_not_called()

    @patch('chatbot.services.requests.post')
    def test_provider_errors_are_safe_and_are_not_retried(self, post):
        for code in [400, 401, 403, 404, 429, 500, 503]:
            with self.subTest(code=code):
                post.reset_mock()
                post.return_value = Mock(status_code=code)
                with self.assertLogs('chatbot.services', level='WARNING') as logs:
                    result = get_chatbot_response('Which scooter suits my planned journey?')
                self.assertEqual(result, FALLBACK)
                self.assertNotIn('fake-provider-key', '\n'.join(logs.output) + result)
                post.assert_called_once()

    @patch('chatbot.services.requests.post')
    def test_timeout_does_not_expose_exception_or_credentials(self, post):
        post.side_effect = requests.Timeout('fake-provider-key should never be shown')
        with self.assertLogs('chatbot.services', level='WARNING') as logs:
            result = get_chatbot_response('Which scooter suits my planned journey?')
        self.assertEqual(result, FALLBACK)
        self.assertNotIn('fake-provider-key', '\n'.join(logs.output) + result)

    @patch('chatbot.services.requests.post')
    def test_empty_blocked_truncated_or_malformed_responses_use_fallback(self, post):
        for body in [{}, {'candidates': []}, {'candidates': [None]},
                     {'candidates': [{'finishReason': 'SAFETY'}]},
                     {'candidates': [{'finishReason': 'MAX_TOKENS'}]},
                     {'candidates': [{'finishReason': 'STOP', 'content': {'parts': []}}]}]:
            with self.subTest(body=body):
                post.return_value = Mock(status_code=200, json=Mock(return_value=body))
                self.assertEqual(get_chatbot_response('Which scooter suits my planned journey?'), FALLBACK)

    @patch('chatbot.services.requests.post')
    def test_provider_thoughts_are_not_shown(self, post):
        post.return_value = self.provider_response(content={'parts': [
            {'thought': True, 'text': 'Internal reasoning'}, {'text': 'Ask our team about your dates.'},
        ]})
        result = get_chatbot_response('Which scooter suits my planned journey?')
        self.assertIn('Ask our team', result)
        self.assertNotIn('Internal reasoning', result)

    @override_settings(GEMINI_MODEL='https://untrusted.example/model')
    @patch('chatbot.services.requests.post')
    def test_invalid_model_never_sends_key_to_another_endpoint(self, post):
        self.assertEqual(get_chatbot_response('Which scooter suits my planned journey?'), FALLBACK)
        post.assert_not_called()

    def test_database_outage_does_not_break_rental_faqs(self):
        with patch('chatbot.services.Bike.objects.filter', side_effect=DatabaseError('private database details')):
            self.assertEqual(public_fleet(), [])
            self.assertIn('5,000', get_chatbot_response('Deposit amount?'))


@override_settings(GEMINI_API_KEY='')
class PublicChatbotTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)

    def test_anonymous_visitor_can_ask_without_login_or_csrf_token(self):
        response = self.client.post(reverse('chat'), {'message': 'How much is the deposit?'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('5,000', response.data['response'])

    def test_invalid_input_is_rejected_before_provider_call(self):
        for message in ['', '   ', None, 7, ['Hello'], 'x' * 801]:
            cache.clear()
            with self.subTest(message=type(message).__name__), patch('chatbot.views.get_chatbot_response') as respond:
                response = self.client.post(reverse('chat'), {'message': message}, format='json')
                self.assertEqual(response.status_code, 400)
                respond.assert_not_called()
        cache.clear()
        response = self.client.post(reverse('chat'), ['Hello'], format='json')
        self.assertEqual(response.status_code, 400)

    def test_chatbot_requests_are_throttled_to_protect_free_quota(self):
        for _ in range(6):
            self.assertEqual(self.client.post(reverse('chat'), {'message': 'Hi'}, format='json').status_code, 200)
        response = self.client.post(reverse('chat'), {'message': 'Hi'}, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)

    def test_other_private_api_permissions_are_unchanged(self):
        response = self.client.get(reverse('mobile_api:dashboard_stats'))
        self.assertEqual(response.status_code, 401)


@override_settings(GEMINI_API_KEY='fake-provider-key', GEMINI_MODEL='gemini-3.5-flash-lite')
class ChatbotConfigurationTests(SimpleTestCase):
    @patch('chatbot.management.commands.check_chatbot.requests.get')
    def test_safe_metadata_check_does_not_generate_text(self, get):
        get.return_value = Mock(status_code=200)
        output = StringIO()
        call_command('check_chatbot', '--check-provider', stdout=output)
        self.assertIn('Model metadata reachable', output.getvalue())
        self.assertNotIn('fake-provider-key', output.getvalue())
        self.assertNotIn('generateContent', get.call_args.args[0])
