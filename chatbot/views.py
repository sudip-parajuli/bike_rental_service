from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import get_chatbot_response

class ChatView(APIView):
    """
    API View to handle chat messages.
    """
    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        response_text = get_chatbot_response(user_message)
        return Response({"response": response_text}, status=status.HTTP_200_OK)
