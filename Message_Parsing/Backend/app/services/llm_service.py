from langchain_google_genai import ChatGoogleGenerativeAI
from app.utils.logging_config import logger
from app.config import GOOGLE_API_KEY
import json
from typing import Optional, Dict, Any

# Initialize LLM
model = None
try:
    
    model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3
)
    # model = ChatGoogleGenerativeAI(
    #     model="gemini-2.0-flash-thinking-exp-01-21",
    #     temperature=0.3,
    #     max_tokens=None,
    #     google_api_key=GOOGLE_API_KEY
    # )
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Gemini model: {e}")
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
    """Analyze message with LLM"""
    if not model:
        logger.warning("LLM model not initialized")
        return None
    
    try:
        prompt = f"""
You are a financial SMS analyzer designed for precise classification and data extraction. Analyze the provided SMS message and return ONLY a valid JSON object with no additional text, markdown, or formatting.

SMS Message: "{message}"

Classify the message into exactly one of these categories based on strict keyword, pattern, and context analysis:
- SALARY_CREDIT: Salary deposits, identified by keywords like 'salary', 'payroll', or employer names with 'credited' and no generic payment context.
- EMI_PAYMENT: Loan EMI payments, identified by keywords like 'EMI', 'loan', 'deducted', 'payment', or loan reference numbers.
- CREDIT_CARD_TRANSACTION: Credit card purchases, identified by keywords like 'credit card', 'spent', 'charged', 'merchant', or authorization codes.
- SIP_INVESTMENT: Mutual fund SIP investments, identified by keywords like 'SIP', 'mutual fund', 'invested', 'folio', or 'NAV'.
- CREDIT_TRANSACTION: Money credited/deposited (excluding salary), identified by keywords like 'NEFT', 'RTGS', 'credited', 'deposited', or 'received' without salary or employer context.
- DEBIT_TRANSACTION: Money debited/withdrawn, identified by keywords like 'debited', 'withdrawn', 'spent', or 'deducted' without EMI or credit card context.
- INSURANCE_PAYMENT: Insurance premium payments, identified by keywords like 'premium', 'paid', 'deducted' with policy number or insurance company, excluding non-transactional renewal confirmations.
- PROMOTIONAL: Advertisements, offers, or non-transactional messages, identified by keywords like 'offer', 'apply', 'discount', or promotional phrases without transactional details.
- OTHER_FINANCIAL: Financial messages not fitting other categories, including non-transactional insurance renewals, balance inquiries, or account updates.

Classification rules:
1. For INSURANCE_PAYMENT, confirm the message indicates an actual payment (e.g., 'premium paid', 'deducted') rather than a renewal confirmation (e.g., 'renewed successfully'). Non-transactional renewals with 'sum insured' amounts should be classified as OTHER_FINANCIAL.
2. Differentiate SALARY_CREDIT from CREDIT_TRANSACTION by checking for salary-specific keywords ('salary', 'payroll') or employer context. Generic credits (e.g., 'NEFT Credit' with a company name but no salary context) are CREDIT_TRANSACTION.
3. Validate transactional intent by checking for payment or transfer indicators (e.g., 'credited', 'debited', 'paid'). Non-transactional messages default to OTHER_FINANCIAL or PROMOTIONAL.
4. Cross-check numerical patterns (e.g., amounts, account numbers, dates) to confirm transaction type.
5. If multiple categories seem applicable, select the most specific based on unique keywords (e.g., 'EMI' for EMI_PAYMENT over DEBIT_TRANSACTION).
6. Default to OTHER_FINANCIAL only if no other category fits after exhaustive checks.

Extract these fields only when explicitly present and relevant to an actual transaction:
- amount: Transaction amount (number, extract only for actual payments or transfers, e.g., 1000.50; exclude 'sum insured' or non-transactional amounts)
- account_number: Account or card number (string, extract last 4 digits or masked number, e.g., 'XXXX1234')
- transaction_date: Date in YYYY-MM-DD format (string, convert from DD/MM/YYYY, DD-MM-YYYY, or textual formats like '12 Jan 2025')
- available_balance: Available balance (number, extract from phrases like 'Avail Bal', 'balance')
- bank_name: Bank name (string, extract from sender ID or message content, e.g., 'HDFC', 'SBI')

Category-specific fields:
- For SALARY_CREDIT: employer (string, extract company/organization name)
- For EMI_PAYMENT: loan_reference (string, extract loan ID or reference number), loan_type (string, e.g., 'home', 'car', 'personal')
- For CREDIT_CARD_TRANSACTION: merchant (string, extract merchant name), authorization_code (string, extract code if present), total_outstanding (number, extract outstanding balance)
- For SIP_INVESTMENT: fund_name (string, extract mutual fund name), folio_number (string, extract folio number), nav_value (number, extract NAV value)
- For INSURANCE_PAYMENT: policy_number (string, extract policy number), insurance_company (string, extract company name), insurance_type (string, e.g., 'life', 'health')
- For PROMOTIONAL: message (string, store the original SMS message)
- For OTHER_FINANCIAL: policy_number (string, for insurance renewals), insurance_company (string), insurance_type (string), sum_insured (number, for non-transactional insurance amounts)

Handle edge cases:
- If a field is not mentioned, set it to null unless inferable from context (e.g., bank name from sender ID like 'HDFCBNK').
- For ambiguous dates (e.g., '01/02/2025'), assume DD/MM/YYYY unless specified otherwise.
- Exclude 'sum insured' amounts from 'amount' field; store in 'sum_insured' for OTHER_FINANCIAL insurance renewals.
- For company names in credits, assume CREDIT_TRANSACTION unless 'salary' or 'payroll' is explicitly mentioned.

Return this exact JSON structure:
{{
  "message_type": "CATEGORY_NAME",
  "extracted_data": {{
    "field1": "value1",
    "field2": value2
  }},
  "important_points": ["point1", "point2", "point3"]
}}

The 'important_points' array should include:
1. Primary reason for the chosen category (e.g., "Contains 'EMI' and loan reference number").
2. Key extracted fields summary (e.g., "Amount: 5000, Bank: HDFC").
3. Any notable context or ambiguity resolved (e.g., "Sum insured amount excluded from transaction amount").

Return only the JSON object, no other text.
# """
#         prompt = f"""
# You are a financial SMS analyzer.

# Analyze this SMS: "{message}"

# Return only a valid JSON object, no text or formatting.

# Classify as one of:
# - SALARY_CREDIT
# - EMI_PAYMENT
# - CREDIT_CARD_TRANSACTION
# - SIP_INVESTMENT
# - CREDIT_TRANSACTION
# - DEBIT_TRANSACTION
# - INSURANCE_PAYMENT
# - PROMOTIONAL
# - OTHER_FINANCIAL

# Extract fields:
# - amount (number)
# - account_number (string)
# - transaction_date (YYYY-MM-DD)
# - available_balance (number)
# - bank_name (string)

# Category-specific fields:
# - SALARY_CREDIT: employer
# - EMI_PAYMENT: loan_reference, loan_type
# - CREDIT_CARD_TRANSACTION: merchant, authorization_code, total_outstanding
# - SIP_INVESTMENT: fund_name, folio_number, nav_value
# - INSURANCE_PAYMENT: policy_number, insurance_company, insurance_type
# - PROMOTIONAL: message (original)

# Return JSON:
# {{
#   "message_type": "CATEGORY_NAME",
#   "extracted_data": {{
#     "field1": "value1",
#     ...
#   }},
#   "important_points": ["point1", "point2", "point3"]
# }}
# """


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
        
        logger.info(f"LLM analysis successful: {result['message_type']}")
        return result
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return None