import re
from typing import Dict, Any, List
from app.utils.string_utils import clean_numeric_string
from app.utils.date_utils import parse_date
from app.utils.logging_config import logger


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
        data.update(extract_sip_data(message))

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
