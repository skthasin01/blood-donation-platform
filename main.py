from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
from typing import Annotated
from database import engine,Sessionlocal
import models
from router import admin,auth,donor_user,blood_request,donations
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind = engine)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(donor_user.router)
app.include_router(blood_request.router)
app.include_router(donations.router)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()
db_dependency = Annotated[Session,Depends(get_db)]


@app.get("/")
def home():
    return {
        "message": "Blood Donation & Emergency Assistance Platform API",
        "status": "running"
    }

