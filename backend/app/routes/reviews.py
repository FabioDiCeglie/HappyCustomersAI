from fastapi import APIRouter, UploadFile, File
from app.controllers.reviews_controller import upload_excel_reviews

router = APIRouter()


@router.post("/upload-excel")
async def upload_excel_reviews_route(
    file: UploadFile = File(...),
    process_with_ai: bool = True,
    send_emails: bool = False
):
    """Upload Excel file with customer reviews for batch processing"""
    return await upload_excel_reviews(
        file=file,
        process_with_ai=process_with_ai,
        send_emails=send_emails
    ) 