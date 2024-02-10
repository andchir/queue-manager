from routes import router as api_router
from config import settings
from fastapi import FastAPI

app = FastAPI(title=settings.app_name)
app.include_router(api_router)
