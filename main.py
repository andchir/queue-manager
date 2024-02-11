from routes import router as api_router
from config import settings
from fastapi import FastAPI

app = FastAPI(title=settings.app_name, swagger_ui_parameters={'persistAuthorization': True})
app.include_router(api_router)
