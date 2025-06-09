import pandas as pd
import io
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
import logging
from datetime import datetime
import re
from functools import lru_cache

from app.services.review_service import create_and_process_review
from app.agents.review_agent import analyze_review

logger = logging.getLogger(__name__)

# Configuration constants
SUPPORTED_EXTENSIONS = ['.xlsx', '.xls', '.csv']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@lru_cache(maxsize=1)
def get_file_config() -> Dict[str, Any]:
    """Get file processing configuration"""
    return {
        'supported_extensions': SUPPORTED_EXTENSIONS,
        'max_file_size': MAX_FILE_SIZE,
        'required_columns': ['customer_name', 'customer_email', 'review']
    }


async def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    config = get_file_config()
    
    # Check file extension
    if not any(file.filename.lower().endswith(ext) for ext in config['supported_extensions']):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported types: {', '.join(config['supported_extensions'])}"
        )
    
    # Check file size
    if file.size and file.size > config['max_file_size']:
        raise HTTPException(
            status_code=400, 
            detail=f"File size too large. Maximum size: {config['max_file_size'] / (1024*1024):.1f}MB"
        )
    
    return True


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


async def parse_excel_file(file: UploadFile) -> pd.DataFrame:
    """Parse Excel file and return DataFrame"""
    try:
        content = await file.read()
        
        # Parse based on file type
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
        
        return df
    
    except Exception as e:
        logger.error(f"Failed to parse file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to parse file: {str(e)}"
        )


def validate_dataframe_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate that the DataFrame has the required columns"""
    config = get_file_config()
    required_columns = config['required_columns']
    
    # Normalize column names (handle different cases and spaces)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Check for required columns
    missing_columns = []
    column_mapping = {}
    
    for col in required_columns:
        found = False
        for df_col in df.columns:
            # Flexible matching for common variations
            if col in df_col or df_col in col:
                column_mapping[col] = df_col
                found = True
                break
            # Handle specific variations
            elif col == 'customer_name' and any(x in df_col for x in ['name', 'customer']):
                column_mapping[col] = df_col
                found = True
                break
            elif col == 'customer_email' and any(x in df_col for x in ['email', 'mail']):
                column_mapping[col] = df_col
                found = True
                break
            elif col == 'review' and any(x in df_col for x in ['review', 'comment', 'feedback']):
                column_mapping[col] = df_col
                found = True
                break
        
        if not found:
            missing_columns.append(col)
    
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}. "
                   f"Required columns: customer_name, customer_email, review. "
                   f"Found columns: {', '.join(df.columns)}"
        )
    
    return column_mapping


async def process_excel_reviews(
    file: UploadFile, 
) -> Dict[str, Any]:
    """Process Excel file with customer reviews"""
    try:
        logger.info(f"📁 Processing Excel file: {file.filename}")
        
        await validate_file(file)
        
        df = await parse_excel_file(file)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file is empty")
        
        logger.info(f"📊 Found {len(df)} rows in Excel file")
        
        # Validate structure
        column_mapping = validate_dataframe_structure(df)
        
        # Process reviews
        results = {
            'total_rows': len(df),
            'processed': 0,
            'errors': [],
            'reviews_created': [],
            'sentiment_summary': {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            },
        }
        
        for index, row in df.iterrows():
            try:
                # Extract data using column mapping
                customer_name = str(row[column_mapping['customer_name']]).strip()
                customer_email = str(row[column_mapping['customer_email']]).strip()
                review_text = str(row[column_mapping['review']]).strip()
                
                # Skip rows with missing essential data
                if not customer_name or customer_name == 'nan':
                    results['errors'].append(f"Row {index + 1}: Missing customer name")
                    continue
                
                if not customer_email or customer_email == 'nan':
                    results['errors'].append(f"Row {index + 1}: Missing customer email")
                    continue
                
                if not review_text or review_text == 'nan':
                    results['errors'].append(f"Row {index + 1}: Missing review text")
                    continue
                
                if not validate_email(customer_email):
                    results['errors'].append(f"Row {index + 1}: Invalid email format: {customer_email}")
                    continue
                
                # Create review
                review_result = await create_and_process_review(
                    customer_name=customer_name,
                    customer_email=customer_email,
                    review_text=review_text,
                )
            
                results['reviews_created'].append(review_result)
                results['processed'] += 1
                
            except Exception as row_error:
                logger.error(f"Failed to process row {index + 1}: {str(row_error)}")
                results['errors'].append(f"Row {index + 1}: {str(row_error)}")
                continue
        
        logger.info(f"✅ Processed {results['processed']} reviews from Excel file")

        for review in results['reviews_created']:
            if review['analysis']['sentiment'] == 'negative':
                results['sentiment_summary']['negative'] += 1
            elif review['analysis']['sentiment'] == 'positive':
                results['sentiment_summary']['positive'] += 1
            else:
                results['sentiment_summary']['neutral'] += 1
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Failed to process Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")