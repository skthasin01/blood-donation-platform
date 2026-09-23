from fastapi import APIRouter, HTTPException
from pydantic import BaseModel,Field
from typing import Optional
from datetime import datetime
from fastapi.responses import JSONResponse


from models import Donation, Donors, BloodRequest,Users
from router.auth import db_dependency, user_dependency


router = APIRouter()

class DonationCreate(BaseModel):
    donor_id: int = Field(..., gt=0, description="Donor ID must be a positive integer")
    blood_request_id: int = Field(..., gt=0, description="Blood request ID must be a positive integer")
    donation_date: Optional[datetime] = Field(default=None, description="Date of donation")
    units_donated: int = Field(..., gt=0, description="Units donated must be greater than 0")


class DonationUpdate(BaseModel):
    donor_id: Optional[int] = Field(default=None, gt=0)
    blood_request_id: Optional[int] = Field(default=None, gt=0)
    donation_date: Optional[datetime] = None
    units_donated: Optional[int] = Field(default=None, gt=0)

@router.post("/donations/create")
def donation_create(user: user_dependency,db:db_dependency,new_donation : DonationCreate):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    donor = db.query(Donors).filter(Donors.id == new_donation.donor_id).first()
    if donor is None:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    blood_r = db.query(BloodRequest).filter(BloodRequest.id == new_donation.blood_request_id).first()
    if blood_r is None:
        raise HTTPException(status_code=400,detail="Blood request not found")
    donation = Donation(
        donor_id=new_donation.donor_id,
        blood_request_id=new_donation.blood_request_id,
        donation_date=(
            new_donation.donation_date
            if new_donation.donation_date
            else datetime.now()
        ),
        units_donated=new_donation.units_donated
    )

    db.add(donation)
    db.commit()
    db.refresh(donation)
    return JSONResponse(status_code=201, content={"message": "Donation created successfully"})


@router.get('/donations/all')
def view_donations(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    donation = db.query(Donation).all()
    return donation

@router.get('/donations/my')
def my_donations(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    donation = db.query(Donation).filter(Donation.donor_id == user['id']).all()

    return donation


@router.get('/donations/{donation_id}')
def view_specific_donations(user:user_dependency,db:db_dependency,donation_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if donation is None:
        raise HTTPException(status_code=404,detail="Donation not Found!!")
    
    return donation

@router.put("/donations/update/{donation_id}")
def donation_update(user: user_dependency,db:db_dependency,donation_data : DonationUpdate,donation_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if donation is None:
        raise HTTPException(status_code=400,detail="Donation not found")

    if donation.donor_id != user["id"]:
        raise HTTPException(status_code=403, detail="You can only update your own donation")
    
    update_data = donation_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(donation, key, value)

    db.commit()
    db.refresh(donation)
    return JSONResponse(status_code=201, content={"message": "Donation Updated successfully"})

@router.delete("/donations/delete/{donation_id}")
def donation_delete(user: user_dependency,db:db_dependency,donation_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if donation is None:
        raise HTTPException(status_code=400,detail="Donation not found")

    if donation.donor_id != user["id"]:
        raise HTTPException(status_code=403, detail="You can only update your own donation")
    
    db.delete(donation)
    db.commit()
    return JSONResponse(status_code=201, content={"message": "Donation Deleted successfully"})


