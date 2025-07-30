
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from bheem_hr.module import HRModule

app = FastAPI(title="HR Module Standalone")

hr = HRModule()
app.include_router(hr.router, prefix="/api/hr")

@app.get("/")
async def root():
    return {"message": "HR module is running independently"}

