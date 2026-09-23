from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import backtest, model, predictions


app = FastAPI(
    title="NFL Intelligence Platform API"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(backtest.router)
app.include_router(model.router)
app.include_router(predictions.router)


@app.get("/")
def root():
    return {
        "message": "NFL Intelligence Platform API"
    }
