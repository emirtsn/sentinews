from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    oauth2_scheme,
)
from src.models.models import (
    SessionLocal, News, User, UserInteraction,
    InteractionType, engine, Base,
)
from src.recommender import get_hybrid_recommendations

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------------------------------
# Pydantic şemaları
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class InteractionLog(BaseModel):
    news_id: int
    interaction_type: InteractionType

class NewsResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    url: str
    category: Optional[str] = None
    sentiment_score: Optional[float] = None
    published_at: Optional[datetime] = None   # datetime — str değil

    class Config:
        from_attributes = True

class PreferencesUpdate(BaseModel):
    preferences: List[str]


# ---------------------------------------------------------------------------
# Uygulama
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SentiNews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_CATEGORIES = {"Technology", "Business", "Sports", "Science", "Health", "Entertainment"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Genel endpointler
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "SentiNews Backend Çalışıyor!"}


@app.get("/news", response_model=List[NewsResponse])
def get_all_news(db: Session = Depends(get_db)):
    return db.query(News).order_by(News.published_at.desc()).all()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.post("/auth/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        preferences=[],
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"access_token": create_access_token({"sub": new_user.email}), "token_type": "bearer"}


@app.post("/auth/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Hatalı e-posta veya şifre.")

    return {"access_token": create_access_token({"sub": user.email}), "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
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


# ---------------------------------------------------------------------------
# Kullanıcı bilgisi
# ---------------------------------------------------------------------------
@app.get("/users/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "preferences": current_user.preferences or [],
    }


@app.get("/users/me/preferences")
def get_preferences(current_user: User = Depends(get_current_user)):
    return {"preferences": current_user.preferences or []}


@app.put("/users/me/preferences")
def update_preferences(
    body: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clean = [p for p in body.preferences if p in VALID_CATEGORIES]
    current_user.preferences = clean
    db.commit()
    return {"preferences": clean}


# ---------------------------------------------------------------------------
# Kişiselleştirilmiş haber akışı
# ---------------------------------------------------------------------------
@app.get("/news/me", response_model=List[NewsResponse])
def get_my_personalized_news(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_hybrid_recommendations(
        user_id=current_user.id,
        user_prefs=current_user.preferences or [],
        db=db,
        limit=50,
    )


# ---------------------------------------------------------------------------
# Etkileşim kaydı
# ---------------------------------------------------------------------------
@app.post("/log-interaction", status_code=201)
def log_interaction(
    body: InteractionLog,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not db.query(News).filter(News.id == body.news_id).first():
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")

    db.add(UserInteraction(
        user_id=current_user.id,
        news_id=body.news_id,
        interaction_type=body.interaction_type,
    ))
    db.commit()

    return {"status": "ok", "interaction_type": body.interaction_type, "news_id": body.news_id}


# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------
@app.get("/debug/me")
def debug_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}