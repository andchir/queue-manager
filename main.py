from routes import router as api_router
from config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.app_name, swagger_ui_parameters={'persistAuthorization': True})
app.include_router(api_router)

origins = [
    'http://localhost',
    'http://localhost:8001',
    'http://localhost:4200',
    'https://api2app.ru',
    'https://api2app.online'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
