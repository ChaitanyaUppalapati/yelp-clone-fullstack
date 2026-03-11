from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_restaurants():
    # TODO: list restaurants with filters
    return {"message": "List restaurants"}


@router.get("/{restaurant_id}")
def get_restaurant(restaurant_id: int):
    # TODO: get a single restaurant
    return {"message": f"Get restaurant {restaurant_id}"}


@router.post("/")
def create_restaurant():
    # TODO: create a restaurant
    return {"message": "Create restaurant"}
