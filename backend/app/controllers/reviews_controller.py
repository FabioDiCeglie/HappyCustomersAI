import logging
from fastapi import HTTPException, UploadFile
from app.services.file_service import process_excel_reviews

logger = logging.getLogger(__name__)


async def upload_excel_reviews(
    file: UploadFile,
):
    """Upload Excel file with customer reviews for batch processing"""
    try:
        logger.info(f"📁 Received Excel file upload: {file.filename}")
        
        result = await process_excel_reviews(
            file=file,
        )
        
        logger.info(f"✅ Excel processing complete: {result['processed']}/{result['total_rows']} reviews processed")
        
        return {
            "message": "Excel file processed successfully",
            "filename": file.filename,
            "results": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Excel upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Excel upload failed: {str(e)}") 