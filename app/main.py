# main.py
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    statuspage,
    monitor,
    auth,
    tags,
    cert,
    info,
    uptime,
    ping,
    database,
    user,
    settings,
    maintenance,
)
from config import settings as app_settings, logger
from app_setup import initialize_app


def parse_cors_origins(value: str) -> list:
    # Browsers send the Origin header without a trailing slash, so
    # "https://example.com/" would never match.
    origins = []
    for origin in value.split(","):
        origin = origin.strip()
        if origin != "*":
            origin = origin.rstrip("/")
        if origin:
            origins.append(origin)
    return origins


app = FastAPI(title=app_settings.PROJECT_NAME, version=app_settings.APP_VERSION)
app.router.redirect_slashes = True

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(app_settings.CORS_ALLOW_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def enforce_https(request: Request, call_next):
    if app_settings.ENFORCE_HTTPS and request.headers.get('x-forwarded-proto', request.url.scheme) != "https":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url)
    response = await call_next(request)
    return response


app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(database.router, prefix="/database", tags=["DataBase"])
app.include_router(monitor.router, prefix="/monitors", tags=["Monitor"])
app.include_router(statuspage.router, prefix="/statuspages", tags=["Status Page"])
app.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
app.include_router(tags.router, prefix="/tags", tags=["Tags"])
app.include_router(cert.router, prefix="/cert_info", tags=["Certification Info"])
app.include_router(info.router, prefix="/info", tags=["Informations"])
app.include_router(ping.router, prefix="/ping", tags=["Ping Average"])
app.include_router(uptime.router, prefix="/uptime", tags=["Uptime"])
app.include_router(auth.router, prefix="/login", tags=["Authentication"])


@app.on_event("startup")
async def startup_event():
    await initialize_app(app)
    logger.info("KumaAPI started...")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
