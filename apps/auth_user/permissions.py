from ninja.security import HttpBearer
from ninja.errors import HttpError
from apps.auth_user.services import verify_token

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        payload = verify_token(token, token_type="access")
        if payload is None:
            raise HttpError(401, "Invalid or expired token")
        return payload

class JWTAuthManager(HttpBearer):
    def authenticate(self, request, token):
        payload = verify_token(token, token_type="access")
        if payload is None:
            raise HttpError(401, "Invalid or expired token")
        if payload['is_manager'] is False:
            raise HttpError(403, "No permission")

        payload["role"] = "manager"

        return payload

class JWTAuthTeamLead(HttpBearer):
    def authenticate(self, request, token):
        payload = verify_token(token, token_type="access")
        if payload is None:
            raise HttpError(401, "Invalid or expired token")
        if payload['is_teamlead'] is False:
            raise HttpError(403, "No permission")

        payload["role"] = "teamlead"

        return payload
