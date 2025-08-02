from fastapi import FastAPI
from app.modules.hr.api.routes import router as hr_router  # adjust if your router is in a different file

app = FastAPI(title="Bheem HR Module")

# Mount your router
app.include_router(hr_router, prefix="/api/hr")

# Optional health check route
@app.get("/")
def health_check():
    return {"status": "HR Module Running"}
