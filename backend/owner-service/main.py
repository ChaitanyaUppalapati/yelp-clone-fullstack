from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.owner import router as owner_router

app = FastAPI(
    title="Owner Service",
    description="Owner dashboard, claim restaurants, analytics.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(owner_router, prefix="/owner", tags=["Owner"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "owner-service"}
