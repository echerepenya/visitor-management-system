from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.security import get_current_user
from src.models.user import User
from src.services.import_service import import_customers_and_cars_from_csv

router = APIRouter(prefix="/api/import", tags=["Import"])


@router.post("/customers-and-cars-from-csv", summary="Import customers and cars from CSV")
async def import_customers_and_cars(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Only superadmins can import data")
    
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        content = await file.read()
        stats = await import_customers_and_cars_from_csv(content, db)
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
