from fastapi import FastAPI
from routes.routes import router
import uvicorn

app = FastAPI(openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
app.include_router(router, prefix="/api")

@app.get("/api/home")
async def root():
    return {"message": "API Home"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
