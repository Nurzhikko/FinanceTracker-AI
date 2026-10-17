
from fastapi import FastAPI

from database import DATABASE_NAME


app = FastAPI(
    title="FinanceTracker AI",
    description="Personal finance management API",
    version="1.0.0"
)

from routers.transactions import router as transactions_router

app.include_router(transactions_router)


from routers.analytics import router as analytics_router

app.include_router(analytics_router)


from routers.auth import router as auth_router

app.include_router(auth_router)



@app.get("/")
def home():
    return {
        "message": "Welcome to FinanceTracker AI!",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }



from models import Transaction

from fastapi import HTTPException

from fastapi.staticfiles import StaticFiles

app.mount(
    "/dashboard",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)
