from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel,Field
from typing import Optional,Literal
from sqlalchemy import or_ 
from datetime import date
from fastapi.responses import JSONResponse

from models import BloodRequest, Users
from router.auth import db_dependency, user_dependency



router = APIRouter()


class BloodRequestCreate(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=50)
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    units_required: int = Field(..., gt=0, description="Units must be greater than 0")
    hospital_name: str = Field(..., min_length=2, max_length=100)
    hospital_address: str = Field(..., min_length=5, max_length=200)
    contact_number: str = Field(..., min_length=10, max_length=15)
    urgency: Literal["low", "normal", "high"] = "normal"


class BloodRequestUpdate(BaseModel):
    patient_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    blood_group: Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]] = None
    units_required: Optional[int] = Field(default=None, gt=0)
    hospital_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    hospital_address: Optional[str] = Field(default=None, min_length=5, max_length=200)
    contact_number: Optional[str] = Field(default=None)
    urgency: Optional[Literal["low", "normal", "high"]] = None
    status: Optional[Literal["pending","approved", "fulfilled", "cancelled"]] = None

@router.post('/bloodrequest/create')
def create_blood_request(user: user_dependency,db:db_dependency , new_blood_request : BloodRequestCreate):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    current_user = db.query(Users).filter(Users.id == user['id']).first()
    if current_user is None:
        raise HTTPException(status_code=404,detail="User not found!!")

    blood_request_model = BloodRequest(
        user_id = user['id'],
        patient_name = new_blood_request.patient_name,
        blood_group = new_blood_request.blood_group,
        units_required = new_blood_request.units_required,
        hospital_name = new_blood_request.hospital_name,
        hospital_address = new_blood_request.hospital_address,
        contact_number = new_blood_request.contact_number,
        urgency = new_blood_request.urgency,
        status = "pending"
    )
    db.add(blood_request_model)
    db.commit()
    db.refresh(blood_request_model)

    return JSONResponse(status_code=201, content={"message": "Blood request created successfully"})

@router.get("/blood-requests")
def get_blood_requests(
    db: db_dependency,
    search: Optional[str] = Query(None, description="Search by patient name, hospital name, or request ID"),
    blood_group: Optional[str] = Query(None, description="Filter by blood group"),
    status: Optional[str] = Query(None, description="Filter by status (pending, fulfilled, etc.)"),
    urgency: Optional[str] = Query(None, description="Filter by urgency (low, medium, high)"),
    start_date: Optional[date] = Query(None, description="Filter requests created after this date"),
    end_date: Optional[date] = Query(None, description="Filter requests created before this date"),
    sort: Literal["newest", "oldest", "hospital_name", "units"] = Query("newest", description="Sort option"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    query = db.query(BloodRequest)
    if search:
        query = query.filter(
            or_(
                BloodRequest.patient_name.ilike(f"%{search}%"),
                BloodRequest.hospital_name.ilike(f"%{search}%"),
                BloodRequest.id.ilike(f"%{search}%")
            )
        )

    if blood_group:
        query = query.filter(BloodRequest.blood_group.ilike(blood_group))

    if status:
        query = query.filter(BloodRequest.status.ilike(status))

    if urgency:
        query = query.filter(BloodRequest.urgency.ilike(urgency))

    if start_date and end_date:
        query = query.filter(BloodRequest.created_at.between(start_date, end_date))

    sort_fields = {
        "newest": BloodRequest.created_at,
        "oldest": BloodRequest.created_at,
        "hospital_name": BloodRequest.hospital_name,
        "units": BloodRequest.units_required
    }

    if sort not in sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort option: {sort}")
        
    if sort == "newest": 
        query = query.order_by( BloodRequest.created_at.desc() )
    elif sort == "oldest": 
        query = query.order_by( BloodRequest.created_at.asc() )
    elif sort == "hospital_name": 
        query = query.order_by( BloodRequest.hospital_name.asc() )
    elif sort == "units": 
        query = query.order_by( BloodRequest.units_required.asc() )

    total = query.count()
    skip = (page - 1) * page_size
    requests = query.offset(skip).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "blood_requests": requests
    }


@router.get('/blood-request/my')
def get_my_blood_request(user: user_dependency,db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    blood_r = db.query(BloodRequest).filter(BloodRequest.user_id == user['id']).all()
    return blood_r

@router.get('/blood-request/{request_id}')
def get_specific_blood_request(user: user_dependency,db : db_dependency,request_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    blood_r = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if blood_r is None:
        raise HTTPException(status_code=404,detail="Blood request not found")
    return blood_r


@router.put('/blood-request/update/{request_id}')
def update_blood_request(user: user_dependency,db : db_dependency,request_id : int,request_data : BloodRequestUpdate):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    blood_r = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if blood_r is None:
        raise HTTPException(status_code=404,detail="Blood request not found")

    if blood_r.user_id != user['id']:
        raise HTTPException(status_code=403,detail="you can only update own blood request")

    update_data = request_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(blood_r, key, value)

    db.commit()
    db.refresh(blood_r)

    return JSONResponse(status_code=201, content={"message": "Blood request Updated successfully"})


@router.delete('/blood-request/delete/{request_id}')
def delete_blood_request(user: user_dependency,db : db_dependency,request_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication")

    blood_r = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if blood_r is None:
        raise HTTPException(status_code=404,detail="Blood request not found")

    if blood_r.user_id != user['id']:
        raise HTTPException(status_code=403,detail="you can only delete own blood request")

    db.delete(blood_r)
    db.commit()

    return JSONResponse(status_code=201, content={"message": "Blood request deleted successfully"})
