import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.models.models import Admin
from app.services.auth_service import auth_service
from app.api.v1.stripe import router as stripe_router
from app.api.v1.reports import router as reports_router
from app.api.v1.admin import router as admin_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for B2C Duovrai love compatibility report analysis.",
    version="1.0.0"
)

# Configure CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Automatically create tables on startup (perfect for instant local development/tests)
@app.on_event("startup")
def configure_db():
    logger.info("Initializing database and creating tables...")
    logger.info(f"Loaded STRIPE_PRICE_ESSENTIEL: '{settings.STRIPE_PRICE_ESSENTIEL}'")
    logger.info(f"Loaded STRIPE_PRICE_PREMIUM: '{settings.STRIPE_PRICE_PREMIUM}'")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
        create_default_admin()
    except Exception as e:
        logger.exception("Failed to initialize database tables:")


def create_default_admin() -> None:
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        logger.warning("Default admin account not configured. Skipping admin creation.")
        return

    db = SessionLocal()
    try:
        existing_admin = db.query(Admin).filter(Admin.email == settings.ADMIN_EMAIL).first()
        if existing_admin:
            logger.info("Default admin already exists: %s", settings.ADMIN_EMAIL)
            return

        admin = Admin(
            email=settings.ADMIN_EMAIL,
            password_hash=auth_service.hash_password(settings.ADMIN_PASSWORD),
            full_name=settings.ADMIN_FULL_NAME,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Default admin account created: %s", settings.ADMIN_EMAIL)
    except Exception:
        logger.exception("Failed to create default admin account.")
        db.rollback()
    finally:
        db.close()

# Mount Api Routers
app.include_router(stripe_router, prefix="/api/v1/stripe", tags=["Stripe Checkout"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports & Orders"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin Panel"])

# Root Landing/Documentation Endpoint
@app.get("/", response_class=HTMLResponse)
def root_index():
    return """
    <html>
        <head>
            <title>Duovrai Backend API</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #2d3748; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 40px 20px; background-color: #f7fafc; }
                .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-top: 5px solid #e53e3e; }
                h1 { color: #4a154b; font-size: 2.2rem; margin-top: 0; }
                .logo { font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; font-family: Georgia, serif; }
                .logo span { color: #e53e3e; }
                code { background: #edf2f7; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 0.95rem; }
                a { color: #e53e3e; text-decoration: none; font-weight: 500; }
                a:hover { text-decoration: underline; }
                .endpoints { list-style: none; padding: 0; margin: 25px 0; }
                .endpoints li { padding: 12px; background: #fff5f5; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #e53e3e; }
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo">Duo<span>vrai</span> Backend</div>
                <h1>Serveur FastAPI Activé 🚀</h1>
                <p>Bienvenue sur l'API de <strong>Duovrai</strong>, la plateforme standalone d'analyses de compatibilité amoureuse premium générées par IA.</p>
                <p>Le backend est opérationnel. Vous pouvez dès maintenant explorer la documentation interactive des routes de paiement Stripe et de génération de PDF.</p>
                
                <h3>Liens utiles :</h3>
                <ul class="endpoints">
                    <li>📖 <strong>Swagger UI :</strong> Accéder à la documentation <a href="/docs">/docs</a></li>
                    <li>📊 <strong>ReDoc :</strong> Accéder à la documentation alternative <a href="/redoc">/redoc</a></li>
                    <li>🩺 <strong>Santé du serveur :</strong> <a href="/health">/health</a></li>
                </ul>
                
                <h3>Développement Local & Simulations Stripe :</h3>
                <p>Puisque le Stripe Mock est activé dans votre <code>.env</code> par défaut, vous pouvez simuler tout le tunnel de paiement de A à Z en appelant <code>POST /api/v1/stripe/checkout</code> puis en suivant l'URL de réussite simulée qui déclenchera la génération de rapport WeasyPrint hors-ligne !</p>
            </div>
        </body>
    </html>
    """

# Health Check Route
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": settings.DATABASE_URL.split("://")[0],
        "stripe_mode": "mock" if settings.STRIPE_API_KEY.startswith("sk_test_mock") else "live",
        "anthropic_mode": "mock" if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY.startswith("sk-ant-api03-dummy") else "live"
    }
