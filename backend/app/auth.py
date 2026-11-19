from datetime import datetime,timedelta,timezone
import jwt
from passlib.context import CryptContext
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from .config import JWT_SECRET,JWT_ALGORITHM
from .database import row

pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
bearer=HTTPBearer(auto_error=False)

def hash_password(v): return pwd.hash(v)
def verify_password(v,h): return pwd.verify(v,h)
def create_token(user):
    return jwt.encode({"sub":str(user["id"]),"role":user["role"],"exp":datetime.now(timezone.utc)+timedelta(hours=12)},JWT_SECRET,algorithm=JWT_ALGORITHM)
def current_user(creds:HTTPAuthorizationCredentials=Depends(bearer)):
    if not creds: raise HTTPException(status_code=401,detail="Authentication required")
    try: data=jwt.decode(creds.credentials,JWT_SECRET,algorithms=[JWT_ALGORITHM]); u=row("SELECT id,name,email,role,created_at FROM users WHERE id=?",(int(data["sub"]),))
    except Exception: u=None
    if not u: raise HTTPException(status_code=401,detail="Invalid or expired token")
    return u
