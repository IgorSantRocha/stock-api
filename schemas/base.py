from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pydantic import BaseModel, field_serializer

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


class BaseSchema(BaseModel):
    """
    Base schema que converte qualquer datetime para America/Sao_Paulo
    SOMENTE na serialização (response).
    """

    @field_serializer("*", when_used="always", check_fields=False)
    def serialize_datetime(self, value):
        if isinstance(value, datetime):
            # garante UTC se vier naive
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)

            return value.astimezone(SAO_PAULO_TZ)

        return value
