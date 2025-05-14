from fastapi import FastAPI
from routes.container_route import container_router as con_router
from routes.auth_route import auth_router
from routes.image_route import image_router as img_router
from routes.volume_route import volume_router as vol_router
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from services.db_service import init_db

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(openapi_url="/app2/openapi.json",
    docs_url="/app2/docs",
    redoc_url="/app2/redoc",
    title="Docker Management API",
    description="APIs to manage Docker Images, Containers, and Volumes",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/app2", tags=["Authentication Operations"])
app.include_router(img_router, prefix="/app2", tags=["Image Operations"])
app.include_router(con_router, prefix="/app2", tags=["Container Operations"])
app.include_router(vol_router, prefix="/app2", tags=["Volume Operations"])

@app.on_event("startup")
def startup_db():
    init_db()

@app.get("/app2/home")
async def root():
    return {"message": "APP2 Home"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
