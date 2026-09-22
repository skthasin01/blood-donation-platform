from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel,Field
from models import Users
from database import Sessionlocal
from typing import Annotated,Optional
from fastapi.responses import JSONResponse
from datetime import timedelta,datetime,timezone

from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt,JWTError

router = APIRouter()

bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')
Oauth2_bearer = OAuth2PasswordBearer(tokenUrl='login')
# openssl rand -hex 32 -> strong secret key generator
SECRET_KEY = 'a2485a5abdb2296b04f1aa8c56e2979166f38bc7ee9723932f9637749257a6f2'
ALGORITHM = 'HS256'

def authenticator_user(username,password,db):
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password,user.hash_password):
        return user
    return False


def create_access_token(username: str,user_id : int,role : str, expires_delta:timedelta):
    encode = {'sub': username,'id': user_id, 'role' : role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(Oauth2_bearer)]):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM] )
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")

        if username is None or user_id is None:
            raise HTTPException(status_code=401,detail="Could not validate credentials")
        return {
            "username": username,
            "id": user_id,
            "role": role
        }
    except JWTError as e:
        raise HTTPException(status_code=401,detail=f"JWT Error: {str(e)}")



def get_db():
    db = Sessionlocal()
    try:
        yield db 
    finally:
        db.close()


db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class User(BaseModel):
    email : str
    username : str
    name : str
    password : str
    phone : str
    gender : str

class updated_user(BaseModel):
    email : Optional[str] = Field(default=None)
    username :  Optional[str] = Field(default=None)
    name :  Optional[str] = Field(default=None)
    phone :  Optional[str] = Field(default=None)
    gender :  Optional[str] = Field(default=None)

class passwordupdate(BaseModel):
    current_password : str
    new_password : str


@router.post('/createuser')
def create_users(db : db_dependency, new_user : User):

    existing_username = db.query(Users).filter(Users.username == new_user.username).first()
    if existing_username:
        raise HTTPException(status_code=400,detail="Username already exists")

    existing_email = db.query(Users).filter(Users.email == new_user.email).first()
    if existing_email:
        raise HTTPException(status_code=400,detail="Email already exists")

    existing_phone = db.query(Users).filter(Users.phone == new_user.phone).first()
    if existing_phone:
        raise HTTPException(status_code=400,detail="Phone number already exists")
    
    user_model = Users(
        email = new_user.email,
        username = new_user.username,
        name = new_user.name,
        hash_password = bcrypt_context.hash(new_user.password),
        phone = new_user.phone,
        gender = new_user.gender,
        is_active = True,
        role = "user"
    )
    
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    
    return JSONResponse(status_code=201, content={"message": "User Created successfully"})


@router.post('/login')
def login_user(db : db_dependency,form_data : Annotated[OAuth2PasswordRequestForm,Depends()]):

    user = authenticator_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=401,detail="Incorrect username or password")
    else:
        token = create_access_token(user.username,user.id,user.role,timedelta(minutes=30))
        return {'access_token':token,'token_type':'bearer'}

@router.put('/updateuser')
def update_users(user: user_dependency, db: db_dependency, update_user: updated_user):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = update_user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user_model, key, value)

    db.commit()
    db.refresh(user_model)

    return JSONResponse(status_code=200, content={"message": "User updated successfully"})


@router.put('/passwordchange')
def update_password(user: user_dependency, db: db_dependency, update_pass: passwordupdate):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt_context.verify(update_pass.current_password, user_model.hash_password):
        raise HTTPException(status_code=401,detail="Wrong password")
    else:
        user_model.hash_password = bcrypt_context.hash(update_pass.new_password)

    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return JSONResponse(status_code=200, content={"message": "password updated successfully"})


@router.get('/user')
def get_user_details( user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    
    current_user = db.query(Users).filter(Users.id == user.get('id')).first()
    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        'id':current_user.id,
        'name' : current_user.name,
        'email':current_user.email,
        'username': current_user.username,
        'gender' : current_user.gender,
        'phone' : current_user.phone,
        'is_active' : current_user.is_active,
        'role' : current_user.role
    }
