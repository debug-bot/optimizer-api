from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)

    def validate(self, attrs):
        name = attrs.get("name")
        first_name = name.split(" ")[0]
        last_name = " ".join(name.split(" ")[1:])
        email = attrs.get("email")

        # Generate or set password here as per your application's requirement
        # For now, let's use a dummy password, but in production, use a secure method
        password = User.objects.make_random_password()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "username": email,  # or some other logic to generate a unique username
            },
        )

        if created:
            user.set_password(password)
            user.save()

        refresh = RefreshToken.for_user(user)
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)
        return attrs
