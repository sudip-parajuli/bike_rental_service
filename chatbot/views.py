from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from .services import get_chatbot_response

class ChatRateThrottle(SimpleRateThrottle):
    scope = 'chatbot'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}

class ChatView(APIView):
    """
    API View to handle chat messages.
    """
    # Public rental information only; no account, booking or payment actions.
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ChatRateThrottle]
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]

    def post(self, request):
        user_message = request.data.get('message') if isinstance(request.data, dict) else None
        if not isinstance(user_message, str) or not user_message.strip():
            return Response({"response": "Please enter a rental question."}, status=status.HTTP_400_BAD_REQUEST)
        user_message = user_message.strip()
        if len(user_message) > 800:
            return Response({"response": "Please keep your question under 800 characters."}, status=status.HTTP_400_BAD_REQUEST)
        
        response_text = get_chatbot_response(user_message)
        return Response({"response": response_text}, status=status.HTTP_200_OK)
