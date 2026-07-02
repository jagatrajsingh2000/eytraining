import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.auth import create_access_token, get_current_user, require_user_id
from app.database import SessionLocal
from app.models import User, UserProfile
from app.schemas import UserCreate, UserLogin, UserProfileCreate

router = APIRouter(prefix="/users", tags=["users"])

TERM_ALIASES = {
    "iron_deficiency": ["iron deficiency", "low iron", "ferritin", "low ferritin", "anaemia", "anemia"],
    "vitamin_d_deficiency": ["vitamin d", "vit d", "d3", "low vitamin d"],
    "vitamin_b12_deficiency": ["b12", "vitamin b12", "low b12"],
    "diabetes": ["diabetes", "diabetic", "blood sugar", "hba1c", "a1c"],
    "hypertension": ["hypertension", "high blood pressure", "bp high"],
    "thyroid": ["thyroid", "tsh", "hypothyroid", "hyperthyroid"],
}

SUPPLEMENT_ALIASES = {
    "iron_tablet": ["iron tablet", "iron supplement", "ferrous", "ferritin tablet"],
    "vitamin_d": ["vitamin d", "d3", "cholecalciferol"],
    "vitamin_b12": ["b12", "vitamin b12", "methylcobalamin"],
    "calcium": ["calcium"],
    "multivitamin": ["multivitamin", "multi vitamin"],
    "protein_powder": ["protein powder", "whey", "plant protein"],
}

PASSWORD_ITERATIONS = 210_000


def user_payload(user: User, has_profile: bool) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_admin": bool(user.is_admin),
        "has_profile": has_profile,
        "access_token": create_access_token(user),
        "token_type": "bearer",
    }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def normalize_terms(text: str | None, aliases: dict[str, list[str]]) -> list[str]:
    if not text:
        return []

    lowered = text.lower()
    normalized = []
    for canonical, terms in aliases.items():
        if any(term in lowered for term in terms):
            normalized.append(canonical)

    has_explicit_separator = any(separator in text for separator in [",", "\n", ";"])
    if not has_explicit_separator:
        return normalized

    for separator in [",", "\n", ";"]:
        text = text.replace(separator, "|")
    for item in text.split("|"):
        item = item.strip().lower()
        if len(item.split()) > 3:
            continue
        token = item.replace(" ", "_").replace("-", "_")
        if token and token not in normalized:
            normalized.append(token)

    return normalized


def merge_unique(*items: list[str] | None) -> list[str]:
    merged = []
    for group in items:
        for item in group or []:
            if item and item not in merged:
                merged.append(item)
    return merged


def normalize_goals(payload: UserProfileCreate) -> list[str]:
    goals = payload.goals or []
    if payload.goal:
        goals = [payload.goal, *goals]
    return merge_unique(goals) or ["maintenance"]


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, iterations, salt, digest = stored_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(candidate, digest)


@router.post("", response_model=dict)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == str(payload.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists. Please login.")

    user = User(
        name=payload.name,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_payload(user, has_profile=False)


@router.post("/signup", response_model=dict)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    return create_user(payload, db)


@router.post("/login", response_model=dict)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).strip().lower()).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Account does not exist. Please sign up to create a new account.",
        )
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return user_payload(user, has_profile=profile is not None)


@router.post("/{user_id}/profile", response_model=dict)
def create_profile(
    user_id: int,
    payload: UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_user_id(user_id, current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    normalized_conditions = merge_unique(
        payload.health_conditions,
        normalize_terms(payload.health_conditions_text, TERM_ALIASES),
    )
    normalized_deficiencies = merge_unique(
        payload.deficiencies,
        normalize_terms(payload.deficiencies_text, TERM_ALIASES),
    )
    normalized_supplements = merge_unique(
        payload.supplements,
        normalize_terms(payload.supplements_text, SUPPLEMENT_ALIASES),
    )
    normalized_goals = normalize_goals(payload)
    primary_goal = normalized_goals[0]

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        profile.goal = primary_goal
        profile.goals = normalized_goals
        profile.diet_type = payload.diet_type
        profile.health_conditions = normalized_conditions
        profile.health_conditions_text = payload.health_conditions_text
        profile.deficiencies = normalized_deficiencies
        profile.deficiencies_text = payload.deficiencies_text
        profile.supplements = normalized_supplements
        profile.supplements_text = payload.supplements_text
        profile.health_report_text = payload.health_report_text
    else:
        profile = UserProfile(
            user_id=user_id,
            goal=primary_goal,
            goals=normalized_goals,
            diet_type=payload.diet_type,
            health_conditions=normalized_conditions,
            health_conditions_text=payload.health_conditions_text,
            deficiencies=normalized_deficiencies,
            deficiencies_text=payload.deficiencies_text,
            supplements=normalized_supplements,
            supplements_text=payload.supplements_text,
            health_report_text=payload.health_report_text,
        )
        db.add(profile)
    db.commit()
    return {
        "user_id": user_id,
        "goal": primary_goal,
        "goals": normalized_goals,
        "diet_type": payload.diet_type,
        "health_conditions": normalized_conditions,
        "health_conditions_text": payload.health_conditions_text or "",
        "deficiencies": normalized_deficiencies,
        "deficiencies_text": payload.deficiencies_text or "",
        "supplements": normalized_supplements,
        "supplements_text": payload.supplements_text or "",
        "has_health_report": bool(payload.health_report_text),
    }


@router.get("/{user_id}/profile", response_model=dict)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_user_id(user_id, current_user)
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "user_id": user_id,
        "goal": profile.goal,
        "goals": profile.goals or ([profile.goal] if profile.goal else []),
        "diet_type": profile.diet_type,
        "health_conditions": profile.health_conditions or [],
        "health_conditions_text": profile.health_conditions_text or "",
        "deficiencies": profile.deficiencies or [],
        "deficiencies_text": profile.deficiencies_text or "",
        "supplements": profile.supplements or [],
        "supplements_text": profile.supplements_text or "",
        "health_report_text": profile.health_report_text or "",
        "health_report_filename": profile.health_report_filename,
    }


@router.post("/{user_id}/profile/report", response_model=dict)
async def upload_health_report(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_user_id(user_id, current_user)
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    content = await file.read()
    try:
        report_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Only text-based report uploads are supported in local MVP. Paste PDF text into the profile form.",
        ) from exc

    profile.health_report_text = report_text[:20000]
    profile.health_report_filename = file.filename
    db.commit()
    return {
        "user_id": user_id,
        "filename": file.filename,
        "characters_saved": len(profile.health_report_text or ""),
    }
