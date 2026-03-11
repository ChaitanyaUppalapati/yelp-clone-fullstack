from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
def get_me():
    # TODO: return current user profile
    return {"message": "Get current user"}


@router.put("/me")
def update_me():
    # TODO: update current user profile
    return {"message": "Update current user"}
