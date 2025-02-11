import json
import jwt
import datetime

class JWTManager:
    def __init__(self, secret_key, algorithm='HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def encode(self, user_id):
        expires_minutes = 30
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.now() + datetime.timedelta(minutes=expires_minutes)
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def decode(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return 'Token has expired'
        except jwt.InvalidTokenError:
            return 'Invalid token'

    def validate_token(self, token):
        if token == "null":
            return False
        result = self.decode(token)
        if isinstance(result, dict) and 'user_id' in result:
            return True, result['user_id']  # Возвращает True и user_id, если токен валиден
        return False, result  # Возвращает False и сообщение об ошибке