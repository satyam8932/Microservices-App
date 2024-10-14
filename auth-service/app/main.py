# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from passlib.context import CryptContext
from . import models, schemas, auth
from .database import engine, get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.post("/signup", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(or_(models.User.email == user.email, models.User.username == user.username)).first()
        print(db_user)
        if db_user is not None:
            return JSONResponse(status_code=409, content={"message" : "User already exists with given email or username"})
        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
            return JSONResponse(status_code=400, content={"message" : "Invalid Credentials"})
        access_token = auth.create_access_token(data={"sub": db_user.username})
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# @app.get("/protected/")
# def read_protected(username: str = Depends(auth.verify_token)):
#     return {"message": f"Hello, {username}"}
