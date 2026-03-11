from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_favorites():
    # TODO: list user's favorite restaurants
    return {"message": "List favorites"}


@router.post("/{restaurant_id}")
def add_favorite(restaurant_id: int):
    # TODO: add restaurant to favorites
    return {"message": f"Add restaurant {restaurant_id} to favorites"}


@router.delete("/{restaurant_id}")
def remove_favorite(restaurant_id: int):
    # TODO: remove restaurant from favorites
    return {"message": f"Remove restaurant {restaurant_id} from favorites"}
