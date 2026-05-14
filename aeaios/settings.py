import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "apps.users",
    "apps.ai_agents",
    "apps.workflows",
    "apps.rag",
    "apps.ml_pipeline",
    "apps.analytics",
    "apps.automation",
    "apps.dashboards",
    "apps.memory",
    "apps.approvals",
    "apps.notifications",
    "apps.multimodal",
    "apps.reports",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "aeaios.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    }
]
WSGI_APPLICATION = "aeaios.wsgi.application"
ASGI_APPLICATION = "aeaios.asgi.application"

if os.getenv("USE_POSTGRES", "False").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "aeaios"),
            "USER": os.getenv("POSTGRES_USER", "aeaios"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "aeaios"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}
CORS_ALLOW_ALL_ORIGINS = DEBUG

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
USE_CELERY = os.getenv("USE_CELERY", "False").lower() == "true"
CELERY_TASK_ALWAYS_EAGER = not USE_CELERY
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_STORE_EAGER_RESULT = False
CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "data" / "chroma"))
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
N8N_WORKFLOW_COMPLETED_WEBHOOK_URL = os.getenv("N8N_WORKFLOW_COMPLETED_WEBHOOK_URL", N8N_WEBHOOK_URL)
N8N_ML_WEBHOOK_URL = os.getenv("N8N_ML_WEBHOOK_URL", N8N_WORKFLOW_COMPLETED_WEBHOOK_URL)
N8N_VISION_WEBHOOK_URL = os.getenv("N8N_VISION_WEBHOOK_URL", N8N_WORKFLOW_COMPLETED_WEBHOOK_URL)
N8N_RAG_WEBHOOK_URL = os.getenv("N8N_RAG_WEBHOOK_URL", N8N_WORKFLOW_COMPLETED_WEBHOOK_URL)
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "True").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "20"))
HF_SUMMARY_MODEL = os.getenv("HF_SUMMARY_MODEL", "sshleifer/distilbart-cnn-12-6")
HF_SUMMARY_LOCAL_FILES_ONLY = os.getenv("HF_SUMMARY_LOCAL_FILES_ONLY", "True").lower() == "true"
HF_SUMMARY_MAX_INPUT_CHARS = int(os.getenv("HF_SUMMARY_MAX_INPUT_CHARS", "6000"))
HF_SUMMARY_MAX_LENGTH = int(os.getenv("HF_SUMMARY_MAX_LENGTH", "360"))
HF_SUMMARY_MIN_LENGTH = int(os.getenv("HF_SUMMARY_MIN_LENGTH", "80"))
YOLO_ENABLED = os.getenv("YOLO_ENABLED", "True").lower() == "true"
YOLO_MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "yolov8n.pt")
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "")
YOLO_ALLOW_MODEL_DOWNLOAD = os.getenv("YOLO_ALLOW_MODEL_DOWNLOAD", "False").lower() == "true"
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.35"))
LORA_ENABLED = os.getenv("LORA_ENABLED", "False").lower() == "true"
LORA_BASE_MODEL = os.getenv("LORA_BASE_MODEL", "sshleifer/tiny-gpt2")
LORA_LOCAL_FILES_ONLY = os.getenv("LORA_LOCAL_FILES_ONLY", "True").lower() == "true"
LORA_OUTPUT_DIR = os.getenv("LORA_OUTPUT_DIR", str(BASE_DIR / "data" / "lora_adapters"))
LORA_MAX_SAMPLES = int(os.getenv("LORA_MAX_SAMPLES", "64"))
LORA_MAX_LENGTH = int(os.getenv("LORA_MAX_LENGTH", "256"))
LORA_MAX_STEPS = int(os.getenv("LORA_MAX_STEPS", "10"))
LORA_BATCH_SIZE = int(os.getenv("LORA_BATCH_SIZE", "1"))
LORA_LEARNING_RATE = float(os.getenv("LORA_LEARNING_RATE", "0.0002"))
LORA_R = int(os.getenv("LORA_R", "8"))
LORA_ALPHA = int(os.getenv("LORA_ALPHA", "16"))
LORA_DROPOUT = float(os.getenv("LORA_DROPOUT", "0.05"))
LORA_TARGET_MODULES = os.getenv("LORA_TARGET_MODULES", "")
