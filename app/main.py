from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.models import user, event, registration
from app.auth.routes import router as auth_router
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from app.auth import routes as auth   
from app.routers import events

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="EventHub API",
        version="1.0.0",
        description="Event Management System backend built with FastAPI and MySQL",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {"tokenUrl": "/auth/token", "scopes": {}}
            },
        }
    }
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# include your routers
app.include_router(auth.router)
app.include_router(events.router)
Base.metadata.create_all(bind=engine)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow ALL frontends
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
