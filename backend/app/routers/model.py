from fastapi import APIRouter

from app.ml import get_model_info
from app.schemas import ModelInfoOut

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/info", response_model=ModelInfoOut)
def model_info():
    return get_model_info()
