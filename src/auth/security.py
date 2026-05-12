from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
load_dotenv()


# Şifreleme algoritması ayarı
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=True)

# JWT Ayarları (Bunu .env dosyana da ekleyebilirsin)
SECRET_KEY = os.getenv("SECRET_KEY", "gizli_anahtar") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password):
    """Şifreyi alır ve hashlenmiş halini döner."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """Girilmiş şifre ile DB'deki hash'i karşılaştırır."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    """Kullanıcı için 30 dakikalık bir giriş anahtarı üretir."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt