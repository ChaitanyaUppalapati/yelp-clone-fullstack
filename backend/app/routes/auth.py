from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
def login():
    # TODO: implement login
    return {"message": "Login endpoint"}


@router.post("/register")
def register():
    # TODO: implement register
    return {"message": "Register endpoint"}
