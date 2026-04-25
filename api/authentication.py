from rest_framework_simplejwt.authentication import JWTAuthentication


class QueryStringJWTAuthentication(JWTAuthentication):
    """
    Allows JWT authentication via Authorization header or `?token=...`.

    The query string fallback is useful for clients that still connect to
    legacy `/ws/...` endpoints using URL params instead of headers.
    """

    def authenticate(self, request):
        header = self.get_header(request)

        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                validated_token = self.get_validated_token(raw_token)
                return self.get_user(validated_token), validated_token

        query_token = request.query_params.get("token")
        if not query_token:
            return None

        validated_token = self.get_validated_token(query_token)
        return self.get_user(validated_token), validated_token
