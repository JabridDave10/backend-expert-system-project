from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

from app.core.middleware import configure_middleware
from app.core.database import create_tables, initialize_default_roles
# from app.modules.citas.routers import health, citas, citas_today
from app.modules.auth.routers.user_router import router as user_router
from app.modules.auth.routers.auth_router import router as auth_router
from app.modules.register.routers.register_router import router as register_router
# from app.modules.assistantAI.routers.assistantAI_router import router as assistantAI_router
# from app.modules.schedules.routers.schedule_router import router as schedule_router
# from app.modules.medical_history.routers.medical_history_router import router as medical_history_router

app = FastAPI(title="Expert System Project - Backend", version="0.1.0")

# Configurar middleware (CORS u otros)
configure_middleware(app)

@app.on_event("startup")
async def startup_event():
    create_tables()
    initialize_default_roles()

# app.include_router(health.router)
# app.include_router(citas.router)  # Main appointments router
# app.include_router(citas.legacy_router)  # Legacy compatibility router
# app.include_router(citas_today.router)  # Today appointments router
# app.include_router(citas_today.legacy_router)  # Today appointments legacy router
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(register_router)
# app.include_router(assistantAI_router)
# app.include_router(schedule_router)
# app.include_router(medical_history_router)

@app.get("/")
@app.head("/")
def read_root():
    return {
        "message": "Backend funcionando 🚀",
        "endpoints": {
            "users": "/users/",
            "auth": "/auth/",
            "register": "/register/",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }
