from langchain_google_genai import ChatGoogleGenerativeAI
from app.utils.logging_config import logger
from app.config import GOOGLE_API_KEY
import json
from typing import Optional, Dict, Any

# Initialize LLM
model = None
try:
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-thinking-exp-01-21",
        temperature=0.3,
        max_tokens=None,
        google_api_key=GOOGLE_API_KEY
    )
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
        
        logger.info(f"LLM analysis successful: {result['message_type']}")
        return result
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return None