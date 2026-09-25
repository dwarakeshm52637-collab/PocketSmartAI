import json

from fastapi import (
    FastAPI,
    Request,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)

from fastapi.responses import (
    HTMLResponse,
    JSONResponse
)

from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from .config import get_settings

from .database import (
    Base,
    engine,
    get_db
)

from .models import (
    User,
    RecommendationHistory
)

from .schemas import (
    RegisterRequest,
    LoginRequest,
    HomeRequest,
    PartyRequest,
    JewelryRequest
)

from .security import (
    COOKIE_NAME,
    create_token,
    get_current_user,
    hash_password,
    verify_password
)

from .ai_service import (
    generate,
    to_dict
)


settings = get_settings()


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)


app.mount(
    "/static",
    StaticFiles(
        directory="app/static"
    ),
    name="static"
)


templates = Jinja2Templates(
    directory="app/templates"
)


@app.get(
    "/",
    response_class=HTMLResponse
)
def index(
    request: Request
):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@app.get(
    "/login",
    response_class=HTMLResponse
)
def login_page(
    request: Request
):

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request
        }
    )


@app.get(
    "/register",
    response_class=HTMLResponse
)
def register_page(
    request: Request
):

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request
        }
    )


@app.get(
    "/dashboard",
    response_class=HTMLResponse
)
def dashboard_page(
    request: Request
):

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request
        }
    )


@app.get(
    "/planner/{category}",
    response_class=HTMLResponse
)
def planner_page(
    category: str,
    request: Request
):

    if category not in {
        "home",
        "party",
        "jewelry"
    }:

        raise HTTPException(
            404,
            "Planner not found"
        )

    return templates.TemplateResponse(
        f"{category}.html",
        {
            "request": request
        }
    )


@app.get(
    "/history",
    response_class=HTMLResponse
)
def history_page(
    request: Request
):

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request
        }
    )


@app.get("/health")
def health():

    return {
        "status": "ok",
        "ai_configured": bool(
            settings.gemini_api_key
        ),
        "model": settings.gemini_model
    }


@app.post("/register")
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):

    email = (
        payload.email
        .lower()
        .strip()
    )

    existing = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing:

        raise HTTPException(
            409,
            "An account with this email already exists."
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(
            payload.password
        )
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    response = JSONResponse(
        {
            "message":
            "Registration successful"
        }
    )

    response.set_cookie(
        COOKIE_NAME,
        create_token(user.id),
        httponly=True,
        samesite="lax",
        max_age=43200
    )

    return response


@app.post("/login")
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.email
            == payload.email.lower().strip()
        )
        .first()
    )

    if (
        not user
        or not verify_password(
            payload.password,
            user.password_hash
        )
    ):

        raise HTTPException(
            401,
            "Invalid email or password."
        )

    response = JSONResponse(
        {
            "message":
            "Login successful"
        }
    )

    response.set_cookie(
        COOKIE_NAME,
        create_token(user.id),
        httponly=True,
        samesite="lax",
        max_age=43200
    )

    return response


@app.post("/logout")
def logout():

    response = JSONResponse(
        {
            "message":
            "Logged out"
        }
    )

    response.delete_cookie(
        COOKIE_NAME
    )

    return response


@app.get("/session-info")
def session_info(
    user: User = Depends(
        get_current_user
    )
):

    return {
        "authenticated": True,

        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@app.get("/session-data")
def session_data(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    count = (
        db.query(
            RecommendationHistory
        )
        .filter_by(
            user_id=user.id
        )
        .count()
    )

    return {
        "user_id": user.id,
        "recommendation_count": count
    }


def save_history(
    db,
    user,
    category,
    request_data,
    response_data
):

    row = RecommendationHistory(

        user_id=user.id,

        category=category,

        request_json=json.dumps(
            request_data,
            ensure_ascii=False
        ),

        response_json=json.dumps(
            response_data,
            ensure_ascii=False
        )
    )

    db.add(row)

    db.commit()


@app.post("/generate-home")
def generate_home(
    payload: HomeRequest,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    data = payload.model_dump()

    result = to_dict(
        generate(
            "home",
            data
        )
    )

    save_history(
        db,
        user,
        "home",
        data,
        result
    )

    return result


@app.post("/generate-party")
def generate_party(
    payload: PartyRequest,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    data = payload.model_dump()

    result = to_dict(
        generate(
            "party",
            data
        )
    )

    save_history(
        db,
        user,
        "party",
        data,
        result
    )

    return result


@app.post("/generate-jewelry")
async def generate_jewelry(

    budget: float = Form(...),

    occasion: str = Form(...),

    style: str = Form("Elegant"),

    metal: str = Form("Any"),

    outfit_notes: str = Form(""),

    outfit_image: UploadFile | None = File(None),

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)
):

    payload = JewelryRequest(

        budget=budget,

        occasion=occasion,

        style=style,

        metal=metal,

        outfit_notes=outfit_notes
    )

    data = payload.model_dump()

    image_bytes = None

    image_mime = None


    if (
        outfit_image
        and outfit_image.filename
    ):

        allowed = {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif"
        }

        if (
            outfit_image.content_type
            not in allowed
        ):

            raise HTTPException(
                400,
                "Upload JPG, PNG, WEBP or GIF only."
            )

        image_bytes = (
            await outfit_image.read()
        )

        if (
            len(image_bytes)
            > settings.max_upload_mb
            * 1024
            * 1024
        ):

            raise HTTPException(
                400,
                f"Image must be smaller than "
                f"{settings.max_upload_mb} MB."
            )

        image_mime = (
            outfit_image.content_type
        )


    result = to_dict(
        generate(
            "jewelry",
            data,
            image_bytes,
            image_mime
        )
    )


    save_history(
        db,
        user,
        "jewelry",
        data,
        result
    )

    return result


@app.get("/history")
def history(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    rows = (
        db.query(
            RecommendationHistory
        )
        .filter_by(
            user_id=user.id
        )
        .order_by(
            RecommendationHistory.created_at.desc()
        )
        .limit(50)
        .all()
    )

    return [

        {
            "id": row.id,

            "category": row.category,

            "created_at":
                row.created_at.isoformat(),

            "request":
                json.loads(
                    row.request_json
                ),

            "result":
                json.loads(
                    row.response_json
                )
        }

        for row in rows
    ]


@app.delete("/history")
def clear_history(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    (
        db.query(
            RecommendationHistory
        )
        .filter_by(
            user_id=user.id
        )
        .delete()
    )

    db.commit()

    return {
        "message":
        "History cleared"
    }


# API aliases

@app.post("/api/auth/register")
def api_register(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):

    return register(
        payload,
        db
    )


@app.post("/api/auth/login")
def api_login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):

    return login(
        payload,
        db
    )


@app.post("/api/auth/logout")
def api_logout():

    return logout()


@app.get("/api/auth/session")
def api_session(
    user: User = Depends(
        get_current_user
    )
):

    return session_info(user)


@app.post("/api/recommendations/home")
def api_home(
    payload: HomeRequest,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return generate_home(
        payload,
        user,
        db
    )


@app.post("/api/recommendations/party")
def api_party(
    payload: PartyRequest,
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return generate_party(
        payload,
        user,
        db
    )


@app.get("/api/history")
def api_history(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return history(
        user,
        db
    )


@app.delete("/api/history")
def api_delete_history(
    user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return clear_history(
        user,
        db
    )