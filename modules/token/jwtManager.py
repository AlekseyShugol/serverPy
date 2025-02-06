import jwt
import datetime

class JWTManager():
    def __init__(self, secret_key,algorithm='HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def encode(self,user_id, expires_minutes = 30):
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.now() + datetime.timedelta(minutes=expires_minutes)
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def decode(self,token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return 'Token has expired'
        except jwt.InvalidTokenError:
            return 'Invalid token'