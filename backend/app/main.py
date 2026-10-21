from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assignments, labs, plans, progress, projects, submissions
from app.db import Base, engine

app = FastAPI(title="Tutor Lab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(plans.router)
app.include_router(assignments.router)
app.include_router(submissions.router)
app.include_router(progress.router)
app.include_router(labs.router)

# Keep local development usable before the Alembic migration is run.
Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"ok": True}

