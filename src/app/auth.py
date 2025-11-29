from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional

# NOTE: put a real secret in env in production
SECRET_KEY = "change_this_secret_for_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

bearer = HTTPBearer()

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": subject, "iat": datetime.utcnow()}
    if expires_delta:
        to_encode.update({"exp": datetime.utcnow() + expires_delta})
    else:
        to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
        return {"sub": subject}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
