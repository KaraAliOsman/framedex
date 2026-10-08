from rest_framework import serializers

from pricing.serializers import StrictSerializer


class MailPreviewSerializer(serializers.Serializer):
    source_id = serializers.UUIDField()
    recipient = serializers.CharField(allow_blank=True)
    reference = serializers.CharField()
    html = serializers.CharField()
    provider = serializers.CharField()


class MailSendSerializer(StrictSerializer):
    expected_source_id = serializers.UUIDField()
    expected_recipient = serializers.EmailField()
    confirmed = serializers.BooleanField()

    def validate_confirmed(self, value):
        if value is not True:
            raise serializers.ValidationError("Confirma el destinatario y el envío.")
        return value


class MailRecoverySerializer(StrictSerializer):
    expected_attempt = serializers.IntegerField(min_value=1)
    confirmed_remote_absence = serializers.BooleanField()

    def validate_confirmed_remote_absence(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Comprueba que el destinatario no recibió el correo antes de reenviar."
            )
        return value


class MailRecordSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    kind = serializers.CharField()
    recipient = serializers.EmailField()
    subject = serializers.CharField()
    project_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    state = serializers.CharField()
    attempt = serializers.IntegerField()
    delivered_at = serializers.DateTimeField(allow_null=True)
    error_code = serializers.CharField(allow_null=True)


class MailIntegrationSerializer(serializers.Serializer):
    provider = serializers.CharField()
    connected = serializers.BooleanField()
    status = serializers.CharField()
    instructions = serializers.CharField()


class MailExampleSerializer(serializers.Serializer):
    kind = serializers.CharField()
    html = serializers.CharField()
