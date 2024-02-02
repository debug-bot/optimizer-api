from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import LoginSerializer
from drf_yasg.utils import swagger_auto_schema


class UserViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for logging users in.
    """

    authentication_classes = []

    @swagger_auto_schema(
        request_body=LoginSerializer, responses={200: "Login successful"}
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            return Response(
                {
                    "user": {
                        "email": user_data["email"],
                        "name": user_data["name"],
                    },
                    "tokens": {
                        "refresh": user_data["refresh"],
                        "access": user_data["access"],
                    },
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
