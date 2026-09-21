from database import Base
from sqlalchemy import Column,Integer,String,Boolean,ForeignKey,Date,DateTime
from datetime import datetime


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String)
    email = Column(String,unique=True)
    username = Column(String,unique=True)
    hash_password = Column(String)
    phone = Column(String,unique=True)
    gender = Column(String)
    is_active = Column(Boolean,default=True)
    role = Column(String,default='user') #admin or user

class Donors(Base):
    __tablename__ = "donors"

    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer,ForeignKey("users.id"),unique=True)
    blood_group = Column(String)
    date_of_birth = Column(Date)
    address = Column(String)
    city = Column(String)
    available = Column(Boolean, default=True)
    last_donation_date = Column(Date)

class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_name = Column(String)
    blood_group = Column(String)
    units_required = Column(Integer)
    hospital_name = Column(String)
    hospital_address = Column(String)
    contact_number = Column(String)
    urgency = Column(String, default="normal")
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.now)

class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey("donors.id"))
    blood_request_id = Column(Integer, ForeignKey("blood_requests.id"))

    donation_date = Column(DateTime, default=datetime.now)
    units_donated = Column(Integer, default=1)