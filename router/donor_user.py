from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from models import Users,Donors
from datetime import date
from typing import Optional
from fastapi.responses import JSONResponse

from router.auth import db_dependency, user_dependency


router = APIRouter()

class DonorCreate(BaseModel):
    blood_group : str
    date_of_birth : date
    address : Optional[str]
    city :str
    available : bool
    last_donation_date : date
  

class DonorUpdate(BaseModel):
    blood_group : Optional[str] = Field(default=None)
    date_of_birth : Optional[date] = Field(default=None)
    address : Optional[str] = Field(default=None)
    city :Optional[str] = Field(default=None)
    available : Optional[bool] = Field(default=None)
    last_donation_date : Optional[date] = Field(default=None)


@router.get("/donor/all")
def get_all_donner(db:db_dependency):
    donors = db.query(Donors).all()
    return donors

@router.post('/donor')
def create_donor(user : user_dependency,db : db_dependency, new_donor : DonorCreate):

    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    if db.query(Donors).filter(Donors.user_id == user['id']).first():
        raise HTTPException(status_code=400,detail="You are already registered as a donor")   

    donor_model = Donors(
        user_id=user["id"], 
        blood_group = new_donor.blood_group,
        date_of_birth = new_donor.date_of_birth,
        address = new_donor.address,
        city = new_donor.city,
        available = new_donor.available,
        last_donation_date = new_donor.last_donation_date
    )
    
    db.add(donor_model)
    db.commit()
    db.refresh(donor_model)
    
    return JSONResponse(status_code=201, content={"message": "Donor Created successfully"})

@router.get('/donor/my')
def my_donor(user : user_dependency,db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    
    donor = db.query(Donors).filter(Donors.user_id == user['id']).first()
    if donor is None:
        raise HTTPException(status_code=404,detail="Donor not found!!")
    
    return donor

@router.get('/donor/{donor_id}')
def specific_donor(user : user_dependency,db : db_dependency, donor_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    
    donor = db.query(Donors).filter(Donors.id == donor_id).first()
    if donor is None:
        raise HTTPException(status_code=404,detail="Donor not found!!")
    
    return donor

@router.put('/donor/update/{donor_id}')
def update_donor(user : user_dependency, db : db_dependency,donor_id : int, donor_data : DonorUpdate):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    donor = db.query(Donors).filter(Donors.id == donor_id).first()
    if donor is None:
        raise HTTPException(status_code=404,detail="Donor not found!!")

    if donor.user_id != user["id"]:
        raise HTTPException(status_code=403,detail="You can only update your own donor profile")

    update_data = donor_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(donor, key, value)

    db.commit()
    db.refresh(donor)   

    return JSONResponse(status_code=201, content={"message": "Donor Updated successfully"})


@router.delete('/donor/delete/{donor_id}')
def delete_donor(user : user_dependency, db : db_dependency,donor_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    donor = db.query(Donors).filter(Donors.id == donor_id).first()
    if donor is None:
        raise HTTPException(status_code=404,detail="Donor not found!!")

    if donor.user_id != user["id"]:
        raise HTTPException(status_code=403,detail="You can only update your own donor profile")


    db.delete(donor)
    db.commit()

    return JSONResponse(status_code=201, content={"message": "Donor Deleted successfully"})
