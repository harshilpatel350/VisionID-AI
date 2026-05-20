from __future__ import annotations
from fastapi.responses import ORJSONResponse

class PrettyORJSONResponse(ORJSONResponse):
    media_type = "application/json"
