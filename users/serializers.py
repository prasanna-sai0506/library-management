from rest_framework import serializers
from django.db.models import Sum
from .models import User
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'credits']
        read_only_fields = ['credits']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 'role', 'credits', 'is_staff']
        read_only_fields = ['id', 'credits', 'is_staff']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        return user


class UserProfileSerializer(UserSerializer):
    total_credits_spent = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['total_credits_spent']

    def get_total_credits_spent(self, user):
        total = user.borrowings.aggregate(total=Sum('credits_spent'))['total']
        return total or 0