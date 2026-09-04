from accounts.serializers import RegisterSerializer

data = {
    'username': 'david',
    'email': 'david@example.com',
    'password': 'testpass123',
    'role': 'STAFF'
}

serializer = RegisterSerializer(data=data)
if serializer.is_valid():
    user = serializer.save()
    print(f"User created: {user.username}")
    print(f"User role: {user.profile.role}")
else:
    print("Errors:", serializer.errors)
