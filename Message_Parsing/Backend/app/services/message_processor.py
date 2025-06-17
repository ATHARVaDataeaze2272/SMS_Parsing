# from datetime import datetime
# from typing import Dict, Any, Optional
# from app.database import get_db
# from app.utils.logging_config import logger
# from app.services.data_extraction import classify_message_type, extract_financial_data, generate_important_points, sanitize_llm_data
# from app.services.llm_service import analyze_with_llm
# from app.utils.date_utils import parse_date

# async def store_financial_data(message_type: str, data: Dict[str, Any], raw_message: str, customer_info: Dict[str, Any], important_points: list[str]):
#     """Store data in MongoDB with better error handling"""
#     db = None
#     try:
#         db = get_db()
        
#         # Store/update customer information
#         customers = db['customers']
#         customer_doc = {
#             'customer_id': customer_info['customer_id'],
#             'name': customer_info['customer_name'],
#             'phone_number': str(customer_info['phone_number']),
#             'updated_at': datetime.utcnow()
#         }
        
#         customers.update_one(
#             {'customer_id': customer_info['customer_id']},
#             {
#                 '$set': customer_doc,
#                 '$setOnInsert': {'created_at': datetime.utcnow()}
#             },
#             upsert=True
#         )
#         logger.info(f"Customer data stored for customer_id: {customer_info['customer_id']}")

#         # Convert transaction_date to datetime object if it's a string
#         if 'transaction_date' in data and data['transaction_date']:
#             if isinstance(data['transaction_date'], str):
#                 try:
#                     data['transaction_date'] = datetime.strptime(data['transaction_date'], '%Y-%m-%d')
#                 except ValueError as e:
#                     logger.warning(f"Failed to convert transaction_date {data['transaction_date']}: {str(e)}")
#                     data['transaction_date'] = None

#         # Store raw message
#         raw_messages = db['raw_messages']
#         raw_message_doc = {
#             'customer_id': customer_info['customer_id'],
#             'message_text': raw_message,
#             'message_type': message_type,
#             'important_points': important_points,
#             'processed': True,
#             'created_at': datetime.utcnow()
#         }
        
#         raw_message_result = raw_messages.insert_one(raw_message_doc)
#         raw_message_id = raw_message_result.inserted_id
#         logger.info(f"Raw message stored with ID: {raw_message_id}")

#         # For promotional messages, only store in raw_messages
#         if message_type == "PROMOTIONAL":
#             logger.info("Promotional message - stored in raw_messages only")
#             return str(raw_message_id)

#         # Store transaction data
#         transaction_doc = {
#             'customer_id': customer_info['customer_id'],
#             'message_type': message_type,
#             'raw_message_id': raw_message_id,
#             'created_at': datetime.utcnow(),
#             **data
#         }

#         transactions = db['transactions']
#         transaction_result = transactions.insert_one(transaction_doc)
#         logger.info(f"Transaction stored with ID: {transaction_result.inserted_id}")

#         return str(raw_message_id)

#     except Exception as e:
#         logger.error(f"MongoDB storage error: {str(e)}")
#         raise
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# async def process_single_message(date_str: str, message: str, customer_info: Dict[str, Any] = None):
#     """Process a single message with improved error handling"""
#     if not message or not message.strip():
#         raise ValueError("Message is empty or blank")
    
#     logger.info(f"Processing message: {message[:100]}...")
    
#     # Try LLM analysis first
#     llm_result = await analyze_with_llm(message)
    
#     if llm_result and llm_result.get("message_type") and llm_result.get("extracted_data"):
#         message_type = llm_result["message_type"]
#         data = sanitize_llm_data(llm_result["extracted_data"])
#         important_points = llm_result.get("important_points", [])
#         logger.info(f"Using LLM analysis - Type: {message_type}")
#     else:
#         # Fallback to regex-based parsing
#         logger.info("Using regex-based parsing")
#         message_type = classify_message_type(message)
#         data = extract_financial_data(message_type, message)
#         important_points = generate_important_points(message_type, data)
    
#     # Ensure transaction_date is set
#     if 'transaction_date' not in data or not data['transaction_date']:
#         if date_str:
#             parsed_date = parse_date(date_str)
#             if parsed_date:
#                 data['transaction_date'] = parsed_date
#             else:
#                 data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
#         else:
#             data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
    
#     # Store in database if customer info provided
#     if customer_info:
#         try:
#             await store_financial_data(message_type, data, message, customer_info, important_points)
#             logger.info(f"Successfully stored data for customer {customer_info['customer_id']}")
#         except Exception as e:
#             logger.error(f"Failed to store data: {e}")
#             raise

#     return {
#         "message_type": message_type,
#         "important_points": important_points,
#         "data": data
#     }




from datetime import datetime
from typing import Dict, Any, Optional
from app.database import get_db
from app.utils.logging_config import logger
from app.services.data_extraction import classify_message_type, extract_financial_data, generate_important_points, sanitize_llm_data
from app.services.llm_service import analyze_with_llm
from app.utils.date_utils import parse_date

# Hardcoded users for fallback (copied from router code for consistency)
HARDCODED_USERS = [
    {
        "customer_id": "CUST001",
        "customer_name": "John Doe",
        "phone_number": "1234567890"
    },
    {
        "customer_id": "CUST002",
        "customer_name": "Jane Smith",
        "phone_number": "0987654321"
    }
]

async def store_financial_data(
    message_type: str,
    data: Dict[str, Any],
    raw_message: str,
    customer_info: Dict[str, Any],
    important_points: list[str],
    from_field: Optional[str] = None
):
    """Store data in MongoDB with better error handling"""
    db = None
    try:
        db = get_db()
        
        # Validate or create customer
        customers = db['customers']
        customer_id = customer_info['customer_id']
        customer = customers.find_one({"customer_id": customer_id}, {"_id": 0})
        
        if not customer:
            # Create new customer if not found
            customer_doc = {
                'customer_id': customer_id,
                'customer_name': customer_info.get('customer_name', f"Customer {customer_id}"),
                'phone_number': customer_info.get('phone_number', f"Unknown-{customer_id}"),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            customers.insert_one(customer_doc)
            logger.info(f"Created new customer: {customer_id}")
        else:
            # Update existing customer
            customer_doc = {
                'customer_id': customer_id,
                'name': customer.get('customer_name', customer_info.get('customer_name', f"Customer {customer_id}")),
                'phone_number': str(customer.get('phone_number', customer_info.get('phone_number', f"Unknown-{customer_id}"))),
                'updated_at': datetime.utcnow()
            }
            customers.update_one(
                {'customer_id': customer_id},
                {'$set': customer_doc},
                upsert=True
            )
            logger.info(f"Updated customer data for customer_id: {customer_id}")

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
            'customer_id': customer_id,
            'message_text': raw_message,
            'message_type': message_type,
            'important_points': important_points,
            'from': from_field,  # Store the 'from' field
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
            'customer_id': customer_id,
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

async def process_single_message(
    date: Optional[str],
    message: str,
    customer_info: Optional[Dict[str, Any]] = None,
    from_field: Optional[str] = None
):
    """Process a single message with improved error handling"""
    if not message or not message.strip():
        raise ValueError("Message is empty or blank")
    
    logger.info(f"Processing message: {message[:100]}...")
    
    # Try LLM analysis first
    llm_result = await analyze_with_llm(message)
    
    if llm_result and llm_result.get("message_type") and llm_result.get("extracted_data"):
        message_type = llm_result["message_type"]
        data = sanitize_llm_data(llm_result["extracted_data"])
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
        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                data['transaction_date'] = parsed_date
            else:
                data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
        else:
            data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
    
    # Use fallback customer info if none provided
    if not customer_info:
        customer_info = random.choice(HARDCODED_USERS)
        logger.info(f"No customer info provided, using fallback: {customer_info['customer_id']}")
    
    # Store in database if customer info is provided
    try:
        raw_message_id = await store_financial_data(
            message_type=message_type,
            data=data,
            raw_message=message,
            customer_info=customer_info,
            important_points=important_points,
            from_field=from_field
        )
        logger.info(f"Successfully stored data for customer {customer_info['customer_id']}")
    except Exception as e:
        logger.error(f"Failed to store data: {e}")
        raise

    return {
        "message_type": message_type,
        "important_points": important_points,
        "data": data,
        "raw_message_id": raw_message_id
    }