from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from database import Sessionlocal
from models import Users, Donors, BloodRequest, Donation
from router.auth import db_dependency, user_dependency
from passlib.context import CryptContext


router = APIRouter()


bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

db = Sessionlocal()

admin = Users(
    name="Admin",
    email="admin@gmail.com",
    username="admin",
    hash_password=bcrypt_context.hash("Admin@123"),
    phone="01700000000",
    gender="male",
    is_active=True,
    role="admin"
)

db.add(admin)
db.commit()
db.refresh(admin)

def check_admin(user):
    if user["role"] != "admin":
        raise HTTPException(status_code=403,detail="Admin access required")

@router.get("/admin/users")
def get_all_users(user: user_dependency,db: db_dependency):

    check_admin(user)

    users = db.query(Users).all()

    return users


@router.get("/admin/speficic-user/{user_id}")
def get_specific_user(user_id: int,user: user_dependency,db: db_dependency):
    check_admin(user)

    current_user = db.query(Users).filter(Users.id == user_id).first()

    if current_user is None:
        raise HTTPException(status_code=404,detail="User not found")

    return current_user

@router.delete("/admin/users/delete/{user_id}")
def delete_user(user_id: int,user: user_dependency,db: db_dependency):

    check_admin(user)

    current_user = db.query(Users).filter(Users.id == user_id).first()

    if current_user is None:
        raise HTTPException(status_code=404,detail="User not found")

    if current_user.id == user["id"]:
        raise HTTPException(status_code=400,detail="Admin cannot delete their own account")

    db.delete(current_user)
    db.commit()

    return JSONResponse(status_code=201, content={"message": "User Deleted successfully"})


@router.get("/admin/donors/all")
def get_all_donors(user: user_dependency,db: db_dependency):

    check_admin(user)
    donors = db.query(Donors).all()
    return donors


@router.delete("/admin/donors/delete/{donor_id}")
def delete_donor(donor_id: int,user: user_dependency,db: db_dependency):

    check_admin(user)

    donor = db.query(Donors).filter(Donors.id == donor_id).first()

    if donor is None:
        raise HTTPException(status_code=404,detail="Donor not found")

    db.delete(donor)
    db.commit()

    return JSONResponse(status_code=201, content={"message": "Donor Deleted successfully"})



@router.get("/admin/blood-requests/all")
def get_all_blood_requests(user: user_dependency,db: db_dependency,status: Optional[str] = None,
                           urgency: Optional[str] = None,blood_group: Optional[str] = None):

    check_admin(user)

    query = db.query(BloodRequest)

    if status:
        query = query.filter(BloodRequest.status == status)

    if urgency:
        query = query.filter(BloodRequest.urgency == urgency)

    if blood_group:
        query = query.filter(BloodRequest.blood_group == blood_group)

    requests = query.order_by(BloodRequest.created_at.desc()).all()

    return requests


@router.put("/admin/blood-requests/status/{request_id}")
def update_blood_request_status(request_id: int,status: str,user: user_dependency,db: db_dependency):

    check_admin(user)

    blood_request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()

    if blood_request is None:
        raise HTTPException(status_code=404,detail="Blood request not found")

    allowed_statuses = ["pending","approved","fulfilled","cancelled"]

    if status not in allowed_statuses:
        raise HTTPException(status_code=400,detail=f"Status must be one of: {allowed_statuses}")

    blood_request.status = status

    db.commit()
    db.refresh(blood_request)

    return JSONResponse(status_code=201,content={"message": "Blood request status updated successfully"})


@router.delete("/admin/blood-requests/delete/{request_id}")
def delete_blood_request(request_id: int,user: user_dependency,db: db_dependency):

    check_admin(user)

    blood_request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()

    if blood_request is None:
        raise HTTPException(status_code=404,detail="Blood request not found")

    db.delete(blood_request)
    db.commit()

    return JSONResponse(status_code=201, content={"message": "Blood request deleted successfully"})


@router.get("/admin/donations/all")
def get_all_donations(user: user_dependency,db: db_dependency):

    check_admin(user)
    donations = db.query(Donation).all()
    return donations


@router.delete("/admin/donations/delete/{donation_id}")
def delete_donation(donation_id: int,user: user_dependency,db: db_dependency):

    check_admin(user)

    donation = db.query(Donation).filter(Donation.id == donation_id).first()

    if donation is None:
        raise HTTPException(status_code=404,detail="Donation not found")

    db.delete(donation)
    db.commit()

    return JSONResponse(status_code=201, content={"message": "Donation deleted successfully"})



@router.get("/admin/dashboard")
def admin_dashboard(user: user_dependency,db: db_dependency):

    check_admin(user)

    total_users = db.query(Users).count()

    total_donors = db.query(Donors).count()

    total_blood_requests = db.query(BloodRequest).count()

    pending_requests = db.query(BloodRequest).filter(BloodRequest.status == "pending").count()

    total_donations = db.query(Donation).count()

    return {
        "total_users": total_users,
        "total_donors": total_donors,
        "total_blood_requests": total_blood_requests,
        "pending_blood_requests": pending_requests,
        "total_donations": total_donations
    }
