from rest_framework import serializers


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password does not match.")
        return value

    def validate_new_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value, self.context['request'].user)
        return value

