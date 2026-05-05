from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, tickets, users
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.services.seed import seed_demo_data

app = FastAPI(title="TicketDesk API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tickets.router)
