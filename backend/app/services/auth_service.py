from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# Bcrypt tiene problemas con la versión de Python 3.13 en algunos entornos.
# Usamos pbkdf2_sha256 como alternativa más compatible si bcrypt falla.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

class AuthService:
    def hash_password(self, password: str) -> str:
        # Bcrypt no soporta passwords de más de 72 bytes. 
        # Pero aquí el problema parece ser la longitud del hash resultante o algo interno de passlib con Python 3.13.
        # Vamos a asegurar que sea string y usar un esquema más simple si falla.
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: str, email: str) -> str:
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "sub": user_id,
            "email": email,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None

auth_service = AuthService()
