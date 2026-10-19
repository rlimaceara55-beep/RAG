from fastapi import APIRouter
from backend.database import db_client
from backend.config import is_supabase_configured, is_openrouter_configured, OPENROUTER_MODEL, EMBEDDING_MODEL_NAME

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health")
def health_check():
    supabase_status = db_client.check_connection()
    return {
        "status": "online",
        "app_name": "RAG + Teophilo",
        "supabase": {
            "configured": is_supabase_configured(),
            "connected": supabase_status["success"],
            "message": supabase_status["message"]
        },
        "openrouter": {
            "configured": is_openrouter_configured(),
            "model": OPENROUTER_MODEL
        },
        "embedding": {
            "engine": "FastEmbed",
            "model": EMBEDDING_MODEL_NAME,
            "dimension": 384
        }
    }
