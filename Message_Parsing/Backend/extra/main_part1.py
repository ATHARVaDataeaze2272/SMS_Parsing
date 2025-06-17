# Continuing from the generate_important_points function...
import os
import certifi
import re
import csv
import json
import logging
import ssl
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi.responses import JSONResponse

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("financial_sms.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")

if not MONGODB_URL:
    logger.error("MONGODB_URL environment variable not set")
    raise ValueError("MONGODB_URL environment variable not set")

if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY environment variable not set")
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# Initialize LLM with better error handling
model = None
try:
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-thinking-exp-01-21",
        temperature=0.3,  # Lower temperature for more consistent output
        max_tokens=None,
        google_api_key=GOOGLE_API_KEY
    )
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Gemini model: {e}")
    # Try with a different model name as fallback
    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.3,
            google_api_key=GOOGLE_API_KEY
        )
        logger.info("Gemini Pro model initialized as fallback")
    except Exception as e2:
        logger.error(f"Failed to initialize any Gemini model: {e2}")
        model = None

# Initialize FastAPI app
app = FastAPI(title="Financial SMS Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CSVUploadRequest(BaseModel):
    file_path: str
    delimiter: str = ","
    has_header: bool = True

class UploadResponse(BaseModel):
    status: str
    message: str
    records_processed: int = 0
    records_failed: int = 0

class ProcessingStatus(BaseModel):
    total: int
    processed: int
    succeeded: int
    failed: int
    status: str

class MessageResponse(BaseModel):
    message_type: str
    important_points: List[str]
    data: Optional[Dict[str, Any]] = None

# Global variable to track processing status
processing_status = {
    "total": 0,
    "processed": 0,
    "succeeded": 0,
    "failed": 0,
    "status": "idle"
}

# MongoDB connection with better error handling
def get_mongo_client():
    try:
        # Parse MongoDB URL to handle different connection formats
        if "mongodb+srv" in MONGODB_URL:
            client = MongoClient(
                MONGODB_URL,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
        else:
            client = MongoClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
        
        # Test connection
        client.admin.command('ping')
        logger.info("MongoDB connection established successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

def get_db():
    client = get_mongo_client()
    return client['financial_sms_db']

# Date parsing utilities
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

def clean_numeric_string(value_str):
    if not value_str:
        return None
    cleaned = str(value_str).replace(',', '').replace(' ', '')
    if cleaned.endswith('.'):
        cleaned = cleaned[:-1]
    if cleaned.count('.') > 1:
        first_dot = cleaned.find('.')
        cleaned = cleaned[:first_dot+1] + cleaned[first_dot+1:].replace('.', '')
    return cleaned

def classify_message_type(message: str) -> str:
    message_lower = message.lower()
    
    # Promotional messages
    promotional_keywords = [
        "offer", "cashback", "discount", "apply now", "get up to",
        "reward", "promo", "deal", "exclusive", "shop now", "click here"
    ]
    if any(keyword in message_lower for keyword in promotional_keywords):
        return "PROMOTIONAL"
    
    # Salary credits
    if "salary" in message_lower and ("credited" in message_lower or "deposited" in message_lower):
        return "SALARY_CREDIT"
    
    # EMI payments
    if ("loan" in message_lower or "emi" in message_lower) and (
        "debited" in message_lower or "deducted" in message_lower or "due on" in message_lower):
        return "EMI_PAYMENT"
    
    # Credit card transactions
    if "credit card" in message_lower or "creditcard" in message_lower or "card member" in message_lower:
        return "CREDIT_CARD_TRANSACTION"
    
    # SIP investments
    if "sip" in message_lower and ("processed" in message_lower or "deducted" in message_lower):
        return "SIP_INVESTMENT"
    
    # Insurance payments
    if "insurance" in message_lower or "premium" in message_lower or "policy" in message_lower:
        return "INSURANCE_PAYMENT"
    
    # General credit/debit transactions
    if "credited" in message_lower or "deposited" in message_lower:
        return "CREDIT_TRANSACTION"
    if "debited" in message_lower or "deducted" in message_lower:
        return "DEBIT_TRANSACTION"
    
    return "OTHER_FINANCIAL"

def extract_financial_data(message_type: str, message: str) -> Dict[str, Any]:
    data = {}
    
    # Extract amount
    amount_patterns = [
        r'(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)',
        r'amount\s*(?:of|:)?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+\.?\d*)',
        r'([\d,]+\.?\d*)\s*(?:INR|Rs\.?|₹)'
    ]
    
    for pattern in amount_patterns:
        amount_match = re.search(pattern, message, re.IGNORECASE)
        if amount_match:
            amount_str = clean_numeric_string(amount_match.group(1))
            if amount_str:
                try:
                    data['amount'] = float(amount_str)
                    break
                except ValueError:
                    continue

    # Extract account number
    account_patterns = [
        r'(?:A/c(?:\s+no)?\.?|Ac(?:\s+no)?\.?|card ending|account)\s*[:\-]?\s*([A-Z0-9]*\d{4})',
        r'a/c\s*([A-Z0-9]*\d{4})',
        r'account\s*([A-Z0-9]*\d{4})'
    ]
    
    for pattern in account_patterns:
        account_match = re.search(pattern, message, re.IGNORECASE)
        if account_match:
            data['account_number'] = account_match.group(1)
            break

    # Extract date
    date_patterns = [
        r'(\d{2}[-/]\d{2}[-/]\d{2,4})',
        r'(\d{2}[-\s][A-Za-z]{3}[-\s]\d{2,4})',
        r'on\s+(\d{2}[-/\s][A-Za-z]{3}[-/\s]\d{2,4})'
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, message)
        if date_match:
            date_str = date_match.group(1)
            parsed_date = parse_date(date_str)
            if parsed_date:
                data['transaction_date'] = parsed_date
                break

    # Extract balance
    balance_patterns = [
        r'(?:Avl bal|available balance|net available balance)[^0-9]*(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)',
        r'balance[^0-9]*(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)'
    ]
    
    for pattern in balance_patterns:
        balance_match = re.search(pattern, message, re.IGNORECASE)
        if balance_match:
            balance_str = clean_numeric_string(balance_match.group(1))
            if balance_str:
                try:
                    data['available_balance'] = float(balance_str)
                    break
                except ValueError:
                    continue

    # Extract bank name
    bank_patterns = [
        r'(?:from|to|by)?\s*([A-Z][A-Za-z\s]+)\s+(?:Bank|BANK|bank)',
        r'([A-Z]{2,4})\s+Bank'
    ]
    
    for pattern in bank_patterns:
        bank_match = re.search(pattern, message)
        if bank_match:
            bank_name = bank_match.group(1).strip()
            if len(bank_name) > 1:
                data['bank_name'] = bank_name + " Bank" if not bank_name.endswith("Bank") else bank_name
                break

    # Message type specific extractions
    if message_type == "SALARY_CREDIT":
        employer_patterns = [
            r'- ([A-Za-z\s]+) -',
            r'from\s+([A-Za-z\s]+)',
            r'salary.*from\s+([A-Za-z\s]+)'
        ]
        for pattern in employer_patterns:
            employer_match = re.search(pattern, message, re.IGNORECASE)
            if employer_match:
                data['employer'] = employer_match.group(1).strip()
                break
        if 'employer' not in data:
            data['employer'] = "Salary Credit"

    elif message_type == "EMI_PAYMENT":
        loan_ref_match = re.search(r'([A-Z0-9]+\d{6,})', message)
        if loan_ref_match:
            data['loan_reference'] = loan_ref_match.group(1)
        
        loan_type_patterns = [
            r'Loan\s+([A-Za-z]+)',
            r'([A-Za-z]+)\s+loan'
        ]
        for pattern in loan_type_patterns:
            loan_type_match = re.search(pattern, message, re.IGNORECASE)
            if loan_type_match:
                data['loan_type'] = loan_type_match.group(1)
                break
        if 'loan_type' not in data:
            data['loan_type'] = "Personal Loan"

    elif message_type == "CREDIT_CARD_TRANSACTION":
        merchant_patterns = [
            r'at\s+([A-Za-z\s]+)\s+on',
            r'spent at\s+([A-Za-z\s]+)',
            r'purchase at\s+([A-Za-z\s]+)'
        ]
        for pattern in merchant_patterns:
            merchant_match = re.search(pattern, message, re.IGNORECASE)
            if merchant_match:
                data['merchant'] = merchant_match.group(1).strip()
                break
        
        auth_code_match = re.search(r'Authorization code[-:]?\s*(\w+)', message)
        if auth_code_match:
            data['authorization_code'] = auth_code_match.group(1)
        
        outstanding_patterns = [
            r'total outstanding is\s+(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)',
            r'outstanding.*(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)'
        ]
        for pattern in outstanding_patterns:
            outstanding_match = re.search(pattern, message, re.IGNORECASE)
            if outstanding_match:
                outstanding_str = clean_numeric_string(outstanding_match.group(1))
                if outstanding_str:
                    try:
                        data['total_outstanding'] = float(outstanding_str)
                        break
                    except ValueError:
                        continue

    elif message_type == "SIP_INVESTMENT":
        sip_data = extract_sip_data(message)
        data.update(sip_data)

    elif message_type == "INSURANCE_PAYMENT":
        policy_patterns = [
            r'policy(?:\s+no\.?| number)?[:\-]?\s*([A-Z0-9]+)',
            r'policy\s*([A-Z0-9]+)'
        ]
        for pattern in policy_patterns:
            policy_match = re.search(pattern, message, re.IGNORECASE)
            if policy_match:
                data['policy_number'] = policy_match.group(1)
                break
        
        companies = ["LIC", "HDFC Life", "ICICI Prudential", "SBI Life", "Tata AIA"]
        for company in companies:
            if company.lower() in message.lower():
                data['insurance_company'] = company
                break
        
        data['insurance_type'] = "Life Insurance"

    elif message_type == "PROMOTIONAL":
        data['message'] = message

    return data

def extract_sip_data(message: str) -> Dict[str, Any]:
    data = {}
    
    # Extract amount
    amount_patterns = [
        r'(?:Rs\.?|INR)\s*([\d,]+\.?\d*)',
        r'SIP.*(?:Rs\.?|INR)\s*([\d,]+\.?\d*)'
    ]
    for pattern in amount_patterns:
        amount_match = re.search(pattern, message)
        if amount_match:
            amount_str = clean_numeric_string(amount_match.group(1))
            if amount_str:
                try:
                    data['amount'] = float(amount_str)
                    break
                except ValueError:
                    continue

    # Extract date
    date_patterns = [
        r'SIP of (\d{2}/\d{2}/\d{4})',
        r'SIP of (\d{2}-\d{2}-\d{4})',
        r'SIP of (\d{2}-[A-Za-z]{3}-\d{2,4})',
        r'(\d{2}[-/]\d{2}[-/]\d{4})',
        r'(\d{2}[-\s][A-Za-z]{3}[-\s]\d{2,4})'
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, message)
        if date_match:
            date_str = date_match.group(1)
            parsed_date = parse_date(date_str)
            if parsed_date:
                data['transaction_date'] = parsed_date
                break

    # Extract folio number
    folio_patterns = [
        r'[Ff]olio\s+([A-Z0-9]+)',
        r'folio.*([A-Z0-9]{8,})'
    ]
    for pattern in folio_patterns:
        folio_match = re.search(pattern, message)
        if folio_match:
            data['folio_number'] = folio_match.group(1)
            break

    # Extract fund name
    fund_patterns = [
        r'in\s+([A-Za-z\s\-]+?)(?:Regular|has been)',
        r'fund\s+([A-Za-z\s\-]+)'
    ]
    for pattern in fund_patterns:
        fund_match = re.search(pattern, message)
        if fund_match:
            data['fund_name'] = fund_match.group(1).strip()
            break

    # Extract NAV
    nav_patterns = [
        r'NAV of\s+([\d\.]+)',
        r'NAV\s*([\d\.]+)'
    ]
    for pattern in nav_patterns:
        nav_match = re.search(pattern, message)
        if nav_match:
            nav_str = clean_numeric_string(nav_match.group(1))
            if nav_str:
                try:
                    data['nav_value'] = float(nav_str)
                    break
                except ValueError:
                    continue

    return data

def sanitize_llm_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and validate data from LLM response"""
    if not isinstance(data, dict):
        return {}
    
    sanitized = {}
    for key, value in data.items():
        if value is None or value == "":
            continue
            
        if key in ['account_number', 'card_number', 'folio_number', 'policy_number', 'loan_reference']:
            sanitized[key] = str(value).strip()
        elif key in ['amount', 'available_balance', 'total_outstanding', 'nav_value']:
            try:
                if isinstance(value, str):
                    cleaned = clean_numeric_string(value)
                    if cleaned:
                        sanitized[key] = float(cleaned)
                elif isinstance(value, (int, float)):
                    sanitized[key] = float(value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert {key} value {value} to float")
        elif isinstance(value, str):
            cleaned = value.strip()
            sanitized[key] = cleaned
        else:
            sanitized[key] = value
    
    return sanitized

def extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM response with better error handling"""
    try:
        # Remove markdown formatting if present
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        # Find JSON block
        start = text.find('{')
        end = text.rfind('}')
        
        if start == -1 or end == -1 or end <= start:
            logger.error("No valid JSON block found in LLM response")
            return None
            
        json_str = text[start:end+1]
        
        # Parse JSON
        try:
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Problematic JSON: {json_str}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting JSON from response: {e}")
        return None

async def analyze_with_llm(message: str) -> Optional[Dict[str, Any]]:
    """Analyze message with LLM - improved version"""
    if not model:
        logger.warning("LLM model not initialized")
        return None
    
    try:
        prompt = f"""
You are a financial SMS analyzer. Analyze this SMS message and return ONLY a valid JSON object with no additional text, markdown, or formatting.

SMS Message: "{message}"

Classify into one of these categories:
- SALARY_CREDIT: Salary deposits
- EMI_PAYMENT: Loan EMI payments  
- CREDIT_CARD_TRANSACTION: Credit card purchases
- SIP_INVESTMENT: Mutual fund SIP investments
- CREDIT_TRANSACTION: Money credited/deposited
- DEBIT_TRANSACTION: Money debited/withdrawn
- INSURANCE_PAYMENT: Insurance premium payments
- PROMOTIONAL: Advertisements, offers, non-transactional messages
- OTHER_FINANCIAL: Other financial messages

Extract relevant data fields:
- amount: Transaction amount (number)
- account_number: Account/card number (string)
- transaction_date: Date in YYYY-MM-DD format (string)
- available_balance: Available balance (number)
- bank_name: Bank name (string)

Category-specific fields:
- For SALARY_CREDIT: employer (string)
- For EMI_PAYMENT: loan_reference (string), loan_type (string)  
- For CREDIT_CARD_TRANSACTION: merchant (string), authorization_code (string), total_outstanding (number)
- For SIP_INVESTMENT: fund_name (string), folio_number (string), nav_value (number)
- For INSURANCE_PAYMENT: policy_number (string), insurance_company (string), insurance_type (string)
- For PROMOTIONAL: message (string - store the original message)

Return this exact JSON structure:
{{
  "message_type": "CATEGORY_NAME",
  "extracted_data": {{
    "field1": "value1",
    "field2": value2
  }},
  "important_points": ["point1", "point2", "point3"]
}}

Return only the JSON object, no other text.
"""

        response = model.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"LLM raw response: {response_text}")
        
        # Extract JSON from response
        result = extract_json_from_response(response_text)
        if not result:
            logger.error("Failed to extract valid JSON from LLM response")
            return None
        
        # Validate required fields
        required_fields = ["message_type", "extracted_data", "important_points"]
        for field in required_fields:
            if field not in result:
                logger.error(f"Missing required field: {field}")
                return None
        
        # Sanitize extracted data
        if isinstance(result.get("extracted_data"), dict):
            result["extracted_data"] = sanitize_llm_data(result["extracted_data"])
        
        logger.info(f"LLM analysis successful: {result['message_type']}")
        return result
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return None


async def store_financial_data(message_type: str, data: Dict[str, Any], raw_message: str, customer_info: Dict[str, Any], important_points: List[str]):
    """Store data in MongoDB with better error handling"""
    db = None
    try:
        db = get_db()
        
        # Store/update customer information
        customers = db['customers']
        customer_doc = {
            'customer_id': customer_info['customer_id'],
            'name': customer_info['customer_name'],
            'phone_number': str(customer_info['phone_number']),
            'updated_at': datetime.utcnow()
        }
        
        customers.update_one(
            {'customer_id': customer_info['customer_id']},
            {
                '$set': customer_doc,
                '$setOnInsert': {'created_at': datetime.utcnow()}
            },
            upsert=True
        )
        logger.info(f"Customer data stored for customer_id: {customer_info['customer_id']}")

        # Convert transaction_date to datetime object if it's a string
        if 'transaction_date' in data and data['transaction_date']:
            if isinstance(data['transaction_date'], str):
                try:
                    data['transaction_date'] = datetime.strptime(data['transaction_date'], '%Y-%m-%d')
                except ValueError as e:
                    logger.warning(f"Failed to convert transaction_date {data['transaction_date']}: {str(e)}")
                    data['transaction_date'] = None

        # Store raw message
        raw_messages = db['raw_messages']
        raw_message_doc = {
            'customer_id': customer_info['customer_id'],
            'message_text': raw_message,
            'message_type': message_type,
            'important_points': important_points,
            'processed': True,
            'created_at': datetime.utcnow()
        }
        
        raw_message_result = raw_messages.insert_one(raw_message_doc)
        raw_message_id = raw_message_result.inserted_id
        logger.info(f"Raw message stored with ID: {raw_message_id}")

        # For promotional messages, only store in raw_messages
        if message_type == "PROMOTIONAL":
            logger.info("Promotional message - stored in raw_messages only")
            return str(raw_message_id)

        # Store transaction data
        transaction_doc = {
            'customer_id': customer_info['customer_id'],
            'message_type': message_type,
            'raw_message_id': raw_message_id,
            'created_at': datetime.utcnow(),
            **data
        }

        transactions = db['transactions']
        transaction_result = transactions.insert_one(transaction_doc)
        logger.info(f"Transaction stored with ID: {transaction_result.inserted_id}")

        return str(raw_message_id)

    except Exception as e:
        logger.error(f"MongoDB storage error: {str(e)}")
        raise
    finally:
        if db is not None and hasattr(db, 'client'):
            db.client.close()

async def process_single_message(date_str: str, message: str, customer_info: Dict[str, Any] = None):
    """Process a single message with improved error handling"""
    if not message or not message.strip():
        raise ValueError("Message is empty or blank")
    
    logger.info(f"Processing message: {message[:100]}...")
    
    # Try LLM analysis first
    llm_result = None
    if model:
        try:
            llm_result = await analyze_with_llm(message)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
    
    if llm_result and llm_result.get("message_type") and llm_result.get("extracted_data"):
        message_type = llm_result["message_type"]
        data = llm_result["extracted_data"]
        important_points = llm_result.get("important_points", [])
        logger.info(f"Using LLM analysis - Type: {message_type}")
    else:
        # Fallback to regex-based parsing
        logger.info("Using regex-based parsing")
        message_type = classify_message_type(message)
        data = extract_financial_data(message_type, message)
        important_points = generate_important_points(message_type, data)
    
    # Ensure transaction_date is set
    if 'transaction_date' not in data or not data['transaction_date']:
        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date:
                data['transaction_date'] = parsed_date
            else:
                data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
        else:
            data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
    
    # Store in database if customer info provided
    if customer_info:
        try:
            await store_financial_data(message_type, data, message, customer_info, important_points)
            logger.info(f"Successfully stored data for customer {customer_info['customer_id']}")
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            raise

    return {
        "message_type": message_type,
        "important_points": important_points,
        "data": data
    }


def generate_important_points(message_type: str, data: Dict[str, Any]) -> List[str]:
    """Generate important points from extracted data"""
    if message_type == "PROMOTIONAL":
        return ["Promotional message received"]
    
    points = []
    
    if data.get("amount"):
        points.append(f"Amount: ₹{data['amount']:,.2f}")
    
    if data.get("transaction_date"):
        if isinstance(data["transaction_date"], str):
            points.append(f"Date: {data['transaction_date']}")
        else:
            points.append(f"Date: {data['transaction_date'].strftime('%Y-%m-%d')}")
    
    if data.get("account_number"):
        points.append(f"Account: {data['account_number']}")
    
    if data.get("available_balance"):
        points.append(f"Available Balance: ₹{data['available_balance']:,.2f}")
    
    if data.get("bank_name"):
        points.append(f"Bank: {data['bank_name']}")
    
    # Message type specific points
    if message_type == "SALARY_CREDIT":
        if data.get("employer"):
            points.append(f"Employer: {data['employer']}")
        points.append("Salary credited to account")
    
    elif message_type == "EMI_PAYMENT":
        if data.get("loan_type"):
            points.append(f"Loan Type: {data['loan_type']}")
        if data.get("loan_reference"):
            points.append(f"Loan Reference: {data['loan_reference']}")
        points.append("EMI payment processed")
    
    elif message_type == "CREDIT_CARD_TRANSACTION":
        if data.get("merchant"):
            points.append(f"Merchant: {data['merchant']}")
        if data.get("total_outstanding"):
            points.append(f"Outstanding: ₹{data['total_outstanding']:,.2f}")
        points.append("Credit card transaction")
    
    elif message_type == "SIP_INVESTMENT":
        if data.get("fund_name"):
            points.append(f"Fund: {data['fund_name']}")
        if data.get("folio_number"):
            points.append(f"Folio: {data['folio_number']}")
        if data.get("nav_value"):
            points.append(f"NAV: {data['nav_value']}")
        points.append("SIP investment processed")
    
    elif message_type == "INSURANCE_PAYMENT":
        if data.get("policy_number"):
            points.append(f"Policy: {data['policy_number']}")
        if data.get("insurance_company"):
            points.append(f"Company: {data['insurance_company']}")
        points.append("Insurance premium paid")
    
    elif message_type == "CREDIT_TRANSACTION":
        points.append("Amount credited to account")
    
    elif message_type == "DEBIT_TRANSACTION":
        points.append("Amount debited from account")
    
    return points if points else ["Financial transaction processed"]

# API Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Financial SMS Analyzer API",
        "status": "running",
        "version": "1.0.0",
        "llm_status": "available" if model else "unavailable"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test MongoDB connection
        db = get_db()
        db.command('ping')
        mongo_status = "connected"
        db.client.close()
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    
    return {
        "api": "healthy",
        "mongodb": mongo_status,
        "llm": "available" if model else "unavailable",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/analyze-message", response_model=MessageResponse)
async def analyze_message(
    message: str = Form(...),
    date: Optional[str] = Form(None),
    customer_id: Optional[str] = Form(None),
    customer_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None)
):
    """Analyze a single SMS message"""
    try:
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Create customer info if provided
        customer_info = None
        if customer_id and customer_name and phone_number:
            customer_info = {
                'customer_id': customer_id,
                'customer_name': customer_name,
                'phone_number': phone_number
            }
        
        # Process the message
        result = await process_single_message(date, message, customer_info)
        
        return MessageResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Message analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/upload-csv", response_model=UploadResponse)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    delimiter: str = Form(","),
    has_header: bool = Form(True)
):
    """Upload and process CSV file containing SMS messages"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Save uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Start background processing
        background_tasks.add_task(
            process_csv_file, 
            temp_file_path, 
            delimiter, 
            has_header
        )
        
        return UploadResponse(
            status="accepted",
            message="CSV file uploaded successfully. Processing started in background."
        )
        
    except Exception as e:
        logger.error(f"CSV upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processing-status", response_model=ProcessingStatus)
async def get_processing_status():
    """Get current processing status"""
    return ProcessingStatus(**processing_status)

@app.get("/customers")
async def get_customers(skip: int = 0, limit: int = 100):
    """Get list of customers"""
    try:
        db = get_db()
        customers = db['customers']
        
        cursor = customers.find({}).skip(skip).limit(limit).sort("created_at", -1)
        customers_list = []
        
        for customer in cursor:
            customer['_id'] = str(customer['_id'])
            if 'created_at' in customer:
                customer['created_at'] = customer['created_at'].isoformat()
            if 'updated_at' in customer:
                customer['updated_at'] = customer['updated_at'].isoformat()
            customers_list.append(customer)
        
        total_count = customers.count_documents({})
        
        db.client.close()
        
        return {
            "customers": customers_list,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/customers/{customer_id}/transactions")
async def get_customer_transactions(
    customer_id: str, 
    skip: int = 0, 
    limit: int = 50,
    message_type: Optional[str] = None
):
    """Get transactions for a specific customer"""
    try:
        db = get_db()
        transactions = db['transactions']
        
        query = {"customer_id": customer_id}
        if message_type:
            query["message_type"] = message_type
        
        cursor = transactions.find(query).skip(skip).limit(limit).sort("created_at", -1)
        transactions_list = []
        
        for transaction in cursor:
            transaction['_id'] = str(transaction['_id'])
            if 'raw_message_id' in transaction:
                transaction['raw_message_id'] = str(transaction['raw_message_id'])
            if 'created_at' in transaction:
                transaction['created_at'] = transaction['created_at'].isoformat()
            if 'transaction_date' in transaction and transaction['transaction_date']:
                if isinstance(transaction['transaction_date'], datetime):
                    transaction['transaction_date'] = transaction['transaction_date'].isoformat()
            transactions_list.append(transaction)
        
        total_count = transactions.count_documents(query)
        
        db.client.close()
        
        return {
            "transactions": transactions_list,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "customer_id": customer_id
        }
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    


@app.get("/customers/{customer_id}/summary")
async def get_customer_summary(customer_id: str):
    """Get transaction summary for a specific customer"""
    db = None
    try:
        db = get_db()
        transactions = db['transactions']
        
        # Aggregate transaction stats by message type
        pipeline = [
            {"$match": {"customer_id": customer_id}},
            {
                "$group": {
                    "_id": "$message_type",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                    "unique_loans": {"$addToSet": "$loan_reference"},
                    "unique_folios": {"$addToSet": "$folio_number"},
                    "unique_policies": {"$addToSet": "$policy_number"},
                    "max_outstanding": {"$max": "$total_outstanding"}
                }
            },
            {
                "$project": {
                    "message_type": "$_id",
                    "count": 1,
                    "total_amount": {"$ifNull": ["$total_amount", 0]},
                    "unique_loans": {"$size": {"$ifNull": ["$unique_loans", []]}},
                    "unique_folios": {"$size": {"$ifNull": ["$unique_folios", []]}},
                    "unique_policies": {"$size": {"$ifNull": ["$unique_policies", []]}},
                    "max_outstanding": {"$ifNull": ["$max_outstanding", 0]},
                    "_id": 0
                }
            },
            {"$sort": {"count": -1}}
        ]
        message_type_stats = list(transactions.aggregate(pipeline))
        
        # Get total transactions
        total_transactions = transactions.count_documents({"customer_id": customer_id})
        
        # Get customer details
        customers = db['customers']
        customer = customers.find_one({"customer_id": customer_id}, {"_id": 0})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if 'created_at' in customer:
            customer['created_at'] = customer['created_at'].isoformat()
        if 'updated_at' in customer:
            customer['updated_at'] = customer['updated_at'].isoformat()
        
        return {
            "customer": customer,
            "total_transactions": total_transactions,
            "message_type_stats": message_type_stats
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching customer summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db is not None and hasattr(db, 'client'):
            db.client.close()

@app.get("/customers/{customer_id}/messages")
async def get_customer_messages(
    customer_id: str, 
    skip: int = 0, 
    limit: int = 50
):
    """Get raw messages for a specific customer"""
    try:
        db = get_db()
        raw_messages = db['raw_messages']
        
        cursor = raw_messages.find({"customer_id": customer_id}).skip(skip).limit(limit).sort("created_at", -1)
        messages_list = []
        
        for message in cursor:
            message['_id'] = str(message['_id'])
            if 'created_at' in message:
                message['created_at'] = message['created_at'].isoformat()
            messages_list.append(message)
        
        total_count = raw_messages.count_documents({"customer_id": customer_id})
        
        db.client.close()
        
        return {
            "messages": messages_list,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "customer_id": customer_id
        }
        
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary including total transactions, investments, and insurance stats"""
    db = None
    try:
        db = get_db()
        
        # Customer statistics
        customers_count = db['customers'].count_documents({})
        
        # Transaction statistics
        transactions = db['transactions']
        total_transactions = transactions.count_documents({})
        
        # Aggregate statistics by message type
        stats_pipeline = [
            {
                "$group": {
                    "_id": "$message_type",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                    "unique_loans": {"$addToSet": "$loan_reference"},
                    "unique_folios": {"$addToSet": "$folio_number"},
                    "unique_policies": {"$addToSet": "$policy_number"},
                    "max_outstanding": {"$max": "$total_outstanding"}
                }
            },
            {
                "$project": {
                    "message_type": "$_id",
                    "count": 1,
                    "total_amount": {"$ifNull": ["$total_amount", 0]},
                    "unique_loans": {"$size": {"$ifNull": ["$unique_loans", []]}},
                    "unique_folios": {"$size": {"$ifNull": ["$unique_folios", []]}},
                    "unique_policies": {"$size": {"$ifNull": ["$unique_policies", []]}},
                    "max_outstanding": {"$ifNull": ["$max_outstanding", 0]},
                    "_id": 0
                }
            },
            {"$sort": {"count": -1}}
        ]
        message_type_stats = list(transactions.aggregate(stats_pipeline))
        
        # Recent activity
        recent_transactions = list(
            transactions.find(
                {},
                {
                    "message_type": 1,
                    "amount": 1,
                    "created_at": 1,
                    "customer_id": 1,
                    "loan_reference": 1,
                    "folio_number": 1,
                    "policy_number": 1,
                    "total_outstanding": 1,
                    "_id": 0
                }
            )
            .sort("created_at", -1)
            .limit(10)
        )
        
        for transaction in recent_transactions:
            if 'created_at' in transaction:
                transaction['created_at'] = transaction['created_at'].isoformat()
        
        return {
            "total_customers": customers_count,
            "total_transactions": total_transactions,
            "message_type_stats": message_type_stats,
            "recent_transactions": recent_transactions
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db is not None and hasattr(db, 'client'):
            db.client.close()

async def process_csv_file(file_path: str, delimiter: str, has_header: bool):
    """Background task to process CSV file"""
    global processing_status
    
    try:
        processing_status["status"] = "processing"
        processing_status["processed"] = 0
        processing_status["succeeded"] = 0
        processing_status["failed"] = 0
        
        logger.info(f"Starting CSV processing: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file, delimiter=delimiter)
            
            if not has_header:
                fieldnames = ['date', 'message', 'customer_id', 'customer_name', 'phone_number']
                file.seek(0)
                csv_reader = csv.DictReader(file, fieldnames=fieldnames, delimiter=delimiter)
            
            # Log headers for debugging
            logger.info(f"CSV headers: {csv_reader.fieldnames}")
            
            # Count total rows
            rows = list(csv_reader)
            processing_status["total"] = len(rows)
            
            logger.info(f"Found {len(rows)} rows to process")
            
            for i, row in enumerate(rows):
                try:
                    # Log raw row for debugging
                    logger.debug(f"Row {i+1}: {row}")
                    
                    # Find message column (case-insensitive)
                    message = None
                    for key in row:
                        if key and key.lower() in ['message', 'body']:
                            message = row[key].strip()
                            break
                    
                    if not message:
                        logger.warning(f"Row {i+1}: Empty or missing message/body, skipping")
                        processing_status["failed"] += 1
                        continue
                    
                    # Find date column (case-insensitive)
                    date_str = None
                    for key in row:
                        if key and key.lower() in ['date', 'time']:
                            date_str = row[key].strip()
                            break
                    
                    customer_id = row.get('customer_id', '').strip()
                    customer_name = row.get('customer_name', '').strip()
                    phone_number = str(row.get('phone_number', '')).strip()
                    
                    # Validate customer info
                    customer_info = None
                    if customer_id and customer_name and phone_number:
                        customer_info = {
                            'customer_id': customer_id,
                            'customer_name': customer_name,
                            'phone_number': phone_number
                        }
                    elif customer_id:
                        customer_info = {
                            'customer_id': customer_id,
                            'customer_name': customer_name or customer_id,
                            'phone_number': phone_number or 'unknown'
                        }
                    else:
                        logger.warning(f"Row {i+1}: Missing customer_id, skipping")
                        processing_status["failed"] += 1
                        continue
                    
                    # Process the message
                    await process_single_message(date_str, message, customer_info)
                    processing_status["succeeded"] += 1
                    logger.info(f"Processed row {i+1}/{len(rows)}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {i+1}: {str(e)}")
                    processing_status["failed"] += 1
                
                processing_status["processed"] += 1
            
            processing_status["status"] = "completed"
            logger.info(f"CSV processing completed. Success: {processing_status['succeeded']}, Failed: {processing_status['failed']}")
            
    except Exception as e:
        logger.error(f"CSV processing error: {str(e)}")
        processing_status["status"] = "error"
    
    finally:
        try:
            os.remove(file_path)
            logger.info(f"Temporary file {file_path} removed")
        except Exception as e:
            logger.warning(f"Could not remove temporary file {file_path}: {str(e)}")





@app.get("/message-type-counts")
async def get_message_type_counts():
    db = None
    try:
        db = get_db()
        pipeline = [
            {"$group": {"_id": "$message_type", "count": {"$sum": 1}}},
            {"$project": {"message_type": "$_id", "count": 1, "_id": 0}}
        ]
        results = list(db['raw_messages'].aggregate(pipeline))
        counts = {item['message_type']: item['count'] for item in results}
        return {"counts": counts}
    except Exception as e:
        logger.error(f"Error fetching message type counts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db is not None and hasattr(db, 'client'):
            db.client.close()


@app.get("/messages")
async def get_messages_by_type(message_type: str, limit: int = 10):
    db = None
    try:
        db = get_db()
        raw_messages = db['raw_messages']
        
        # Query for promotional messages
        if message_type == "PROMOTIONAL":
            pipeline = [
                {"$match": {"message_type": "PROMOTIONAL"}},
                {
                    "$project": {
                        "message": "$message_text",
                        "important_points": "$important_points",
                        "_id": 0
                    }
                },
                {"$limit": limit}
            ]
            messages = list(raw_messages.aggregate(pipeline))
            return messages
        
        # Query for other message types
        transactions = db['transactions']
        pipeline = [
            {"$match": {"message_type": message_type}},
            {
                "$lookup": {
                    "from": "raw_messages",
                    "localField": "raw_message_id",
                    "foreignField": "_id",
                    "as": "raw_message"
                }
            },
            {"$unwind": "$raw_message"},
            {
                "$project": {
                    "message": "$raw_message.message_text",
                    "extracted_data": {
                        "amount": "$amount",
                        "transaction_date": "$transaction_date",
                        "account_number": "$account_number",
                        "url": "$url"
                    },
                    "_id": 0
                }
            },
            {"$limit": limit}
        ]
        messages = list(transactions.aggregate(pipeline))
        for msg in messages:
            if msg['extracted_data'].get('transaction_date'):
                if isinstance(msg['extracted_data']['transaction_date'], datetime):
                    msg['extracted_data']['transaction_date'] = msg['extracted_data']['transaction_date'].strftime('%Y-%m-%d')
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages by type {message_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db is not None and hasattr(db, 'client'):
            db.client.close()


            
# Error handlers


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Financial SMS Analyzer API...")
    
    # Test database connection on startup
    try:
        test_db = get_db()
        test_db.command('ping')
        logger.info("Database connection test successful")
        test_db.client.close()
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True,
        
    )



















