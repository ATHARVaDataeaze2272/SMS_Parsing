from datetime import datetime
import re
from typing import Optional
from app.utils.logging_config import logger

def parse_date(date_str: str) -> Optional[str]:
    if not date_str:
        return None
        
    try:
        date_str = str(date_str).strip()
        
        # Try ISO 8601 format
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Pattern for DD-MMM-YY or DD MMM YY
        pattern1 = re.compile(r'(\d{1,2})[-\s/]([A-Za-z]{3})[-\s/](\d{2,4})')
        match1 = pattern1.search(date_str)
        if match1:
            day, month_str, year = match1.groups()
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = month_map.get(month_str.upper(), '01')
            if len(year) == 2:
                year = f"20{year}"
            day = day.zfill(2)
            return f"{year}-{month}-{day}"

        # Pattern for DD/MM/YYYY or DD-MM-YYYY
        pattern2 = re.compile(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})')
        match2 = pattern2.search(date_str)
        if match2:
            day, month, year = match2.groups()
            day = day.zfill(2)
            month = month.zfill(2)
            return f"{year}-{month}-{day}"

        # Try various datetime formats
        formats = ["%d-%b-%y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%y-%m-%d", "%d-%b-%Y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {str(e)}")
        return None