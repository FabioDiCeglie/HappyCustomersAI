import logging
from fastapi import HTTPException, UploadFile
from app.services.file_service import file_service

logger = logging.getLogger(__name__)


async def upload_excel_reviews(
    file: UploadFile,
    process_with_ai: bool = True,
    send_emails: bool = False
):
    """Upload Excel file with customer reviews for batch processing"""
    try:
        logger.info(f"📁 Received Excel file upload: {file.filename}")
        
        # Process the Excel file
        result = await file_service.process_excel_reviews(
            file=file,
            process_with_ai=process_with_ai,
            send_emails=send_emails
        )
        
        logger.info(f"✅ Excel processing complete: {result['processed']}/{result['total_rows']} reviews processed")
        
        return {
            "message": "Excel file processed successfully",
            "filename": file.filename,
            "results": result
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        logger.error(f"❌ Excel upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Excel upload failed: {str(e)}") 