from fastapi import APIRouter, UploadFile, File
from app.controllers.reviews_controller import upload_excel_reviews

router = APIRouter()


@router.post("/upload-excel")
async def upload_excel_reviews_route(
    file: UploadFile = File(...),
):
    """Upload Excel file with customer reviews for batch processing"""
    return await upload_excel_reviews(
        file=file,
    ) 