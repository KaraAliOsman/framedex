from rest_framework import serializers

from jobs.registry import register
from notifications.service import dispatch


class MailJobSerializer(serializers.Serializer):
    mail_id = serializers.UUIDField()


@register("mail.deliver", roles=(), payload_serializer=MailJobSerializer, label="Enviar correo")
def deliver_job(payload, context, report):
    report(10)
    result = dispatch(org_id=context.org_id, mail_id=payload["mail_id"])
    report(100)
    return {"state": result["state"]}
