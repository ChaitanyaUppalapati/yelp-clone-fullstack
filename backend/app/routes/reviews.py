from fastapi import APIRouter

router = APIRouter()


@router.get("/restaurant/{restaurant_id}")
def get_reviews(restaurant_id: int):
    # TODO: list reviews for a restaurant
    return {"message": f"Reviews for restaurant {restaurant_id}"}


@router.post("/")
def create_review():
    # TODO: create a review
    return {"message": "Create review"}


@router.delete("/{review_id}")
def delete_review(review_id: int):
    # TODO: delete a review
    return {"message": f"Delete review {review_id}"}
