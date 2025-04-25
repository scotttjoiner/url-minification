# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

import logging
import jwt
from jwt import PyJWKClient
from flask import request
from src import settings
from functools import wraps

log = logging.getLogger(__name__)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        # Local debugging. You should NOT have this set in production!
        if settings.FLASK_DEBUG:
            return f(*args, **kwargs)

        auth_header = request.headers.get('Authorization', '')
        parts = auth_header.split()

        # For compliance, we typically obfuscate the exact reason a request is invalid
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return {'message': 'Unauthorized'}, 401

        token = parts[1]
        
        try:
            
            # Retrieve the signing key from the JWKS endpoint
            jwks_client = PyJWKClient(settings.IDP_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token).key

            # Decode and validate the token. This verifies the signature,
            # token expiration, audience, and (optionally) issuer.
            decoded = jwt.decode(
                token,
                signing_key,
                algorithms = settings.IDP_ALG,
                audience = settings.IDP_AUDIENCE_AUDIENCE
            )

            log.debug('User token for request: {request.path}\n{decoded}')

        except Exception as e:
            
            log.warning(f'Token validation error: {str(e)}')
            return {'message': 'Unauthorized'}, 401

        # Set the decoded token in the request context (or Flask's g)
        # to allow downstream code to access token info.
        request.decoded_token = decoded
        
        # Logging which user did what: assume 'sub' holds the user identifier.
        user_id = decoded.get('sub', 'unknown')
        log.info(f'User: {user_id} accessed {request.path}')
        
        return f(*args, **kwargs)

    return decorated
