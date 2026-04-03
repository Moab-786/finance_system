from fastapi import FastAPI
from app.routers import auth, transactions, analytics

app = FastAPI(title="Finance Tracking System", version="1.0.0")

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "Finance Tracking System API", "docs": "/docs"}