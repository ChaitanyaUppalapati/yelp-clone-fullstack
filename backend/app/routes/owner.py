from fastapi import APIRouter

router = APIRouter()


@router.get("/restaurants")
def owner_restaurants():
    # TODO: list restaurants owned by current user
    return {"message": "Owner's restaurants"}


@router.put("/restaurants/{restaurant_id}")
def update_restaurant(restaurant_id: int):
    # TODO: update restaurant details
    return {"message": f"Update restaurant {restaurant_id}"}


@router.delete("/restaurants/{restaurant_id}")
def delete_restaurant(restaurant_id: int):
    # TODO: delete a restaurant
    return {"message": f"Delete restaurant {restaurant_id}"}
