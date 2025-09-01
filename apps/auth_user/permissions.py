from ninja.security import HttpBearer
from ninja.errors import HttpError
from apps.auth_user.services import verify_token

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        payload = verify_token(token, token_type="access")
        if payload is None:
            raise HttpError(401, "Invalid or expired token")
        return payload
