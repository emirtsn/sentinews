from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from src.models import models 
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from src.auth.security import get_password_hash 
from fastapi import HTTPException, Depends
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.security import verify_password, create_access_token
from src.auth.security import SECRET_KEY, ALGORITHM, oauth2_scheme
from jose import jwt, JWTError

# Kendi modellerimizi ve veritabanı ayarlarımızı içeri aktarıyoruz
from src.models.models import SessionLocal, News, User, engine, Base

from dotenv import load_dotenv
load_dotenv()

# Kullanıcı kayıt olurken gelecek veri yapısı
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

# Giriş sonrası dönecek token yapısı
class Token(BaseModel):
    access_token: str
    token_type: str


Base.metadata.create_all(bind=engine)

app = FastAPI(title="SentiNews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "SentiNews Backend Çalışıyor!"}

@app.get("/news")
def get_all_news(db: Session = Depends(get_db)):
    """
    Veritabanındaki tüm haberleri listeleyen endpoint.
    """
    news_list = db.query(News).all()
    return news_list


@app.post("/auth/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Kullanıcı zaten var mı kontrol et
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")
    
    # 2. Şifreyi hashle ve yeni kullanıcıyı oluştur
    hashed_pass = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_pass,
        full_name=user.full_name,
        preferences=[] # Başlangıçta boş ilgi alanı
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 3. Kayıt sonrası hemen bir token üretip dönelim
    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}



@app.post("/auth/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Kullanıcıyı bul
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # 2. Kullanıcı yoksa veya şifre yanlışsa hata ver
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Hatalı e-posta veya şifre.")
    
    # 3. Giriş başarılı, token'ı ver
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Kullanıcının getirdiği bileti (token) senin gizli anahtarınla açıyoruz
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Geçersiz kimlik.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Oturum süresi dolmuş.")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return user


@app.get("/news/me")
def get_my_personalized_news(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Kullanıcının ilgi alanlarını alıyoruz (JSON formatında sakladığımız liste)
    user_prefs = current_user.preferences 
    
    # 2. Eğer kullanıcı henüz tercih seçmemişse, genel bir haber akışı dönelim
    if not user_prefs:
        return db.query(News).order_by(News.published_at.desc()).limit(10).all()
    
    # 3. Tercih edilen kategorileri filtrele + Keşif için birkaç tane de farklı kategoriden ekle
    # (Sadece sevdiklerini değil, yeni şeyler de görmesini sağlıyoruz)
    personalized_list = db.query(News).filter(News.category.in_(user_prefs)).limit(15).all()
    
    # Keşif (Variety) için rastgele haberler ekleme
    random_discovery = db.query(News).filter(~News.category.in_(user_prefs)).limit(5).all()
    
    return personalized_list + random_discovery