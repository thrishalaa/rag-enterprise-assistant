from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.app.auth import create_access_token

router = APIRouter()

# Hardcoded credentials (change this!)
VALID_USERNAME = "admin"
VALID_PASSWORD = "admin123"

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest):
    if data.username != VALID_USERNAME or data.password != VALID_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token(subject=data.username)
    return {"access_token": token, "token_type": "bearer"}
