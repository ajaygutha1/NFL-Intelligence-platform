from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml import get_model_info
from app.models import ModelInsight
from app.schemas import ModelInfoOut, ModelInsightOut

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/info", response_model=ModelInfoOut)
def model_info():
    return get_model_info()


@router.get("/insights", response_model=list[ModelInsightOut])
def model_insights(db: Session = Depends(get_db)):
    return (
        db.query(ModelInsight)
        .order_by(ModelInsight.permutation_importance.desc())
        .all()
    )
