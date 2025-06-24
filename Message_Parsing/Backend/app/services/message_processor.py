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




# from datetime import datetime
# from typing import Dict, Any, Optional
# from app.database import get_db
# from app.utils.logging_config import logger
# from app.services.data_extraction import classify_message_type, extract_financial_data, generate_important_points, sanitize_llm_data
# from app.services.llm_service import analyze_with_llm
# from app.utils.date_utils import parse_date

# # Hardcoded users for fallback (copied from router code for consistency)
# HARDCODED_USERS = [
#     {
#         "customer_id": "CUST001",
#         "customer_name": "John Doe",
#         "phone_number": "1234567890"
#     },
#     {
#         "customer_id": "CUST002",
#         "customer_name": "Jane Smith",
#         "phone_number": "0987654321"
#     }
# ]

# async def store_financial_data(
#     message_type: str,
#     data: Dict[str, Any],
#     raw_message: str,
#     customer_info: Dict[str, Any],
#     important_points: list[str],
#     from_field: Optional[str] = None
# ):
#     """Store data in MongoDB with better error handling"""
#     db = None
#     try:
#         db = get_db()
        
#         # Validate or create customer
#         customers = db['customers']
#         customer_id = customer_info['customer_id']
#         customer = customers.find_one({"customer_id": customer_id}, {"_id": 0})
        
#         if not customer:
#             # Create new customer if not found
#             customer_doc = {
#                 'customer_id': customer_id,
#                 'customer_name': customer_info.get('customer_name', f"Customer {customer_id}"),
#                 'phone_number': customer_info.get('phone_number', f"Unknown-{customer_id}"),
#                 'created_at': datetime.utcnow(),
#                 'updated_at': datetime.utcnow()
#             }
#             customers.insert_one(customer_doc)
#             logger.info(f"Created new customer: {customer_id}")
#         else:
#             # Update existing customer
#             customer_doc = {
#                 'customer_id': customer_id,
#                 'name': customer.get('customer_name', customer_info.get('customer_name', f"Customer {customer_id}")),
#                 'phone_number': str(customer.get('phone_number', customer_info.get('phone_number', f"Unknown-{customer_id}"))),
#                 'updated_at': datetime.utcnow()
#             }
#             customers.update_one(
#                 {'customer_id': customer_id},
#                 {'$set': customer_doc},
#                 upsert=True
#             )
#             logger.info(f"Updated customer data for customer_id: {customer_id}")

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
#             'customer_id': customer_id,
#             'message_text': raw_message,
#             'message_type': message_type,
#             'important_points': important_points,
#             'from': from_field,  # Store the 'from' field
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
#             'customer_id': customer_id,
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

# async def process_single_message(
#     date: Optional[str],
#     message: str,
#     customer_info: Optional[Dict[str, Any]] = None,
#     from_field: Optional[str] = None
# ):
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
#         if date:
#             parsed_date = parse_date(date)
#             if parsed_date:
#                 data['transaction_date'] = parsed_date
#             else:
#                 data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
#         else:
#             data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
    
#     # Use fallback customer info if none provided
#     if not customer_info:
#         customer_info = random.choice(HARDCODED_USERS)
#         logger.info(f"No customer info provided, using fallback: {customer_info['customer_id']}")
    
#     # Store in database if customer info is provided
#     try:
#         raw_message_id = await store_financial_data(
#             message_type=message_type,
#             data=data,
#             raw_message=message,
#             customer_info=customer_info,
#             important_points=important_points,
#             from_field=from_field
#         )
#         logger.info(f"Successfully stored data for customer {customer_info['customer_id']}")
#     except Exception as e:
#         logger.error(f"Failed to store data: {e}")
#         raise

#     return {
#         "message_type": message_type,
#         "important_points": important_points,
#         "data": data,
#         "raw_message_id": raw_message_id
#     }







# from datetime import datetime
# from typing import Dict, Any, Optional
# import random
# import json
# import os
# import asyncio
# from app.database import get_db
# from app.utils.logging_config import logger
# from app.services.data_extraction import classify_message_type, extract_financial_data, generate_important_points, sanitize_llm_data
# from app.services.llm_service import analyze_with_llm
# from app.utils.date_utils import parse_date

# # Hardcoded users for fallback (copied from router code for consistency)
# HARDCODED_USERS = [
#     {
#         "customer_id": "CUST001",
#         "customer_name": "John Doe",
#         "phone_number": "1234567890"
#     },
#     {
#         "customer_id": "CUST002",
#         "customer_name": "Jane Smith",
#         "phone_number": "0987654321"
#     }
# ]

# async def check_duplicate_sms(sms_id: str, customer_id: str) -> bool:
#     """Check if SMS with given smsId already exists for the customer"""
#     if not sms_id:  # If no sms_id provided, don't check for duplicates
#         return False
        
#     db = None
#     try:
#         db = get_db()
#         raw_messages = db['raw_messages']
        
#         existing_message = raw_messages.find_one({
#             "sms_id": sms_id,
#             "customer_id": customer_id
#         })
        
#         if existing_message:
#             logger.info(f"Duplicate SMS found - smsId: {sms_id}, customer: {customer_id}")
#             return True
#         else:
#             logger.debug(f"No duplicate found for smsId: {sms_id}, customer: {customer_id}")
#             return False
        
#     except Exception as e:
#         logger.error(f"Error checking duplicate SMS: {str(e)}")
#         return False  # In case of error, allow processing to continue
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             try:
#                 db.client.close()
#             except:
#                 pass

# async def get_or_create_customer(customer_id: str, customer_name: Optional[str] = None, phone_number: Optional[str] = None) -> Dict[str, Any]:
#     """Get existing customer or create new one if not found"""
#     db = None
#     try:
#         db = get_db()
#         customers = db['customers']
        
#         # Try to find existing customer
#         customer = customers.find_one({"customer_id": customer_id}, {"_id": 0})
        
#         if customer:
#             logger.info(f"Found existing customer: {customer_id}")
#             return {
#                 'customer_id': customer['customer_id'],
#                 'customer_name': customer.get('customer_name', customer.get('name', f"Customer {customer_id}")),
#                 'phone_number': str(customer.get('phone_number', f"Unknown-{customer_id}"))
#             }
#         else:
#             # Create new customer
#             new_customer = {
#                 'customer_id': customer_id,
#                 'customer_name': customer_name or f"Customer {customer_id}",
#                 'phone_number': phone_number or f"Unknown-{customer_id}",
#                 'created_at': datetime.utcnow(),
#                 'updated_at': datetime.utcnow()
#             }
            
#             result = customers.insert_one(new_customer.copy())
#             logger.info(f"Created new customer: {customer_id} with MongoDB ID: {result.inserted_id}")
            
#             return {
#                 'customer_id': new_customer['customer_id'],
#                 'customer_name': new_customer['customer_name'],
#                 'phone_number': new_customer['phone_number']
#             }
            
#     except Exception as e:
#         logger.error(f"Error in get_or_create_customer: {str(e)}")
#         raise
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             try:
#                 db.client.close()
#             except:
#                 pass

# async def store_financial_data(
#     message_type: str,
#     data: Dict[str, Any],
#     raw_message: str,
#     customer_info: Dict[str, Any],
#     important_points: list[str],
#     from_field: Optional[str] = None,
#     sms_id: Optional[str] = None
# ):
#     """Store data in MongoDB with better error handling and debugging"""
#     db = None
#     try:
#         logger.info(f"Starting to store financial data for customer: {customer_info['customer_id']}")
#         db = get_db()
#         customer_id = customer_info['customer_id']
        
#         # Check for duplicate SMS if sms_id is provided
#         if sms_id:
#             logger.info(f"Checking for duplicate SMS: {sms_id}")
#             is_duplicate = await check_duplicate_sms(sms_id, customer_id)
#             if is_duplicate:
#                 logger.info(f"Duplicate SMS detected - smsId: {sms_id}, customer: {customer_id}")
#                 return None  # Skip processing duplicate
        
#         # Get or create customer (this handles both existing and new customers)
#         logger.info(f"Getting or creating customer: {customer_id}")
#         customer_data = await get_or_create_customer(
#             customer_id=customer_id,
#             customer_name=customer_info.get('customer_name'),
#             phone_number=customer_info.get('phone_number')
#         )
#         logger.info(f"Customer data obtained: {customer_data}")

#         # Convert transaction_date to datetime object if it's a string
#         if 'transaction_date' in data and data['transaction_date']:
#             if isinstance(data['transaction_date'], str):
#                 try:
#                     data['transaction_date'] = datetime.strptime(data['transaction_date'], '%Y-%m-%d')
#                     logger.debug(f"Converted transaction_date to datetime: {data['transaction_date']}")
#                 except ValueError as e:
#                     logger.warning(f"Failed to convert transaction_date {data['transaction_date']}: {str(e)}")
#                     data['transaction_date'] = None

#         # Get fresh database connection for storing raw message
#         db = get_db()
#         raw_messages = db['raw_messages']
        
#         # Prepare raw message document
#         raw_message_doc = {
#             'customer_id': customer_id,
#             'message_text': raw_message,
#             'message_type': message_type,
#             'important_points': important_points,
#             'from': from_field,
#             'sms_id': sms_id,
#             'processed': True,
#             'created_at': datetime.utcnow()
#         }
        
#         logger.info(f"Inserting raw message document: {raw_message_doc}")
        
#         # Insert raw message
#         try:
#             raw_message_result = raw_messages.insert_one(raw_message_doc)
#             raw_message_id = raw_message_result.inserted_id
#             logger.info(f"Raw message stored successfully with ID: {raw_message_id}, smsId: {sms_id}")
#         except Exception as e:
#             logger.error(f"Failed to insert raw message: {str(e)}")
#             logger.error(f"Raw message document was: {raw_message_doc}")
#             raise

#         # For promotional messages, only store in raw_messages
#         if message_type == "PROMOTIONAL":
#             logger.info("Promotional message - stored in raw_messages only")
#             return str(raw_message_id)

#         # Store transaction data
#         transaction_doc = {
#             'customer_id': customer_id,
#             'message_type': message_type,
#             'raw_message_id': raw_message_id,
#             'sms_id': sms_id,
#             'created_at': datetime.utcnow(),
#             **data  # Spread the extracted data
#         }

#         logger.info(f"Inserting transaction document: {transaction_doc}")
        
#         try:
#             transactions = db['transactions']
#             transaction_result = transactions.insert_one(transaction_doc)
#             logger.info(f"Transaction stored successfully with ID: {transaction_result.inserted_id}")
#         except Exception as e:
#             logger.error(f"Failed to insert transaction: {str(e)}")
#             logger.error(f"Transaction document was: {transaction_doc}")
#             raise

#         return str(raw_message_id)

#     except Exception as e:
#         logger.error(f"MongoDB storage error: {str(e)}")
#         logger.error(f"Error details - message_type: {message_type}, customer_id: {customer_info.get('customer_id')}")
#         raise
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             try:
#                 db.client.close()
#             except:
#                 pass

# async def process_single_message(
#     date: Optional[str],
#     message: str,
#     customer_info: Optional[Dict[str, Any]] = None,
#     from_field: Optional[str] = None,
#     sms_id: Optional[str] = None
# ):
#     """Process a single message with improved error handling"""
#     try:
#         if not message or not message.strip():
#             raise ValueError("Message is empty or blank")
        
#         logger.info(f"Processing message: {message[:100]}...")
#         logger.info(f"Customer info: {customer_info}")
#         logger.info(f"SMS ID: {sms_id}")
        
#         # Try LLM analysis first
#         try:
#             llm_result = await analyze_with_llm(message)
#             logger.info(f"LLM analysis result: {llm_result}")
#         except Exception as e:
#             logger.warning(f"LLM analysis failed: {str(e)}")
#             llm_result = None
        
#         if llm_result and llm_result.get("message_type") and llm_result.get("extracted_data"):
#             message_type = llm_result["message_type"]
#             data = sanitize_llm_data(llm_result["extracted_data"])
#             important_points = llm_result.get("important_points", [])
#             logger.info(f"Using LLM analysis - Type: {message_type}, Data: {data}")
#         else:
#             # Fallback to regex-based parsing
#             # logger.info("Using regex-based parsing")
#             # message_type = classify_message_type(message)
#             # data = extract_financial_data(message_type, message)
#             # important_points = generate_important_points(message_type, data)
#             # logger.info(f"Regex analysis - Type: {message_type}, Data: {data}")
#             logger.info("LLM Based Parsing Failed Due to limit")
        
#         # Ensure transaction_date is set
#         if 'transaction_date' not in data or not data['transaction_date']:
#             if date:
#                 parsed_date = parse_date(date)
#                 if parsed_date:
#                     data['transaction_date'] = parsed_date
#                 else:
#                     data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
#             else:
#                 data['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
        
#         # Use fallback customer info if none provided
#         if not customer_info:
#             customer_info = random.choice(HARDCODED_USERS)
#             logger.info(f"No customer info provided, using fallback: {customer_info['customer_id']}")
        
#         # Store in database
#         logger.info(f"About to store financial data...")
#         raw_message_id = await store_financial_data(
#             message_type=message_type,
#             data=data,
#             raw_message=message,
#             customer_info=customer_info,
#             important_points=important_points,
#             from_field=from_field,
#             sms_id=sms_id
#         )
        
#         if raw_message_id is None:
#             # This means it was a duplicate SMS
#             logger.info(f"Duplicate SMS skipped: {sms_id}")
#             return {
#                 "status": "duplicate",
#                 "message": "Duplicate SMS skipped",
#                 "sms_id": sms_id
#             }
            
#         logger.info(f"Successfully stored data for customer {customer_info['customer_id']}")
        
#         return {
#             "message_type": message_type,
#             "important_points": important_points,
#             "data": data,
#             "raw_message_id": raw_message_id,
#             "status": "processed"
#         }
        
#     except Exception as e:
#         logger.error(f"Error in process_single_message: {str(e)}")
#         logger.error(f"Message: {message[:100]}")
#         logger.error(f"Customer info: {customer_info}")
#         raise

# # Add a test function to verify database connectivity
# async def test_database_connection():
#     """Test database connection and collection creation"""
#     db = None
#     try:
#         logger.info("Testing database connection...")
#         db = get_db()
        
#         # Test collections
#         collections = db.list_collection_names()
#         logger.info(f"Existing collections: {collections}")
        
#         # Test inserting a simple document
#         test_collection = db['test_collection']
#         test_doc = {"test": "data", "timestamp": datetime.utcnow()}
#         result = test_collection.insert_one(test_doc)
#         logger.info(f"Test document inserted with ID: {result.inserted_id}")
        
#         # Clean up test document
#         test_collection.delete_one({"_id": result.inserted_id})
#         logger.info("Test document deleted")
        
#         logger.info("Database connection test successful")
#         return True
        
#     except Exception as e:
#         logger.error(f"Database connection test failed: {str(e)}")
#         return False
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             try:
#                 db.client.close()
#             except:
#                 pass





from datetime import datetime
from typing import Dict, Any, Optional
import random
import json
import os
import asyncio
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

async def check_duplicate_sms(sms_id: str, customer_id: str) -> bool:
    """Check if SMS with given smsId already exists for the customer"""
    if not sms_id:  # If no sms_id provided, don't check for duplicates
        return False
        
    db = None
    try:
        db = get_db()
        raw_messages = db['raw_messages']
        
        existing_message = raw_messages.find_one({
            "sms_id": sms_id,
            "customer_id": customer_id
        })
        
        if existing_message:
            logger.info(f"Duplicate SMS found - smsId: {sms_id}, customer: {customer_id}")
            return True
        else:
            logger.debug(f"No duplicate found for smsId: {sms_id}, customer: {customer_id}")
            return False
        
    except Exception as e:
        logger.error(f"Error checking duplicate SMS: {str(e)}")
        return False  # In case of error, allow processing to continue
    finally:
        if db is not None and hasattr(db, 'client'):
            try:
                db.client.close()
            except:
                pass

async def get_or_create_customer(customer_id: str, customer_name: Optional[str] = None, phone_number: Optional[str] = None) -> Dict[str, Any]:
    """Get existing customer or create new one if not found"""
    db = None
    try:
        db = get_db()
        customers = db['customers']
        
        # Try to find existing customer
        customer = customers.find_one({"customer_id": customer_id}, {"_id": 0})
        
        if customer:
            logger.info(f"Found existing customer: {customer_id}")
            return {
                'customer_id': customer['customer_id'],
                'customer_name': customer.get('customer_name', customer.get('name', f"Customer {customer_id}")),
                'phone_number': str(customer.get('phone_number', f"Unknown-{customer_id}"))
            }
        else:
            # Create new customer
            new_customer = {
                'customer_id': customer_id,
                'customer_name': customer_name or f"Customer {customer_id}",
                'phone_number': phone_number or f"Unknown-{customer_id}",
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = customers.insert_one(new_customer.copy())
            logger.info(f"Created new customer: {customer_id} with MongoDB ID: {result.inserted_id}")
            
            return {
                'customer_id': new_customer['customer_id'],
                'customer_name': new_customer['customer_name'],
                'phone_number': new_customer['phone_number']
            }
            
    except Exception as e:
        logger.error(f"Error in get_or_create_customer: {str(e)}")
        raise
    finally:
        if db is not None and hasattr(db, 'client'):
            try:
                db.client.close()
            except:
                pass

async def store_financial_data(
    message_type: str,
    data: Dict[str, Any],
    raw_message: str,
    customer_info: Dict[str, Any],
    important_points: list[str],
    from_field: Optional[str] = None,
    sms_id: Optional[str] = None
):
    """Store data in MongoDB with better error handling and debugging"""
    db = None
    try:
        logger.info(f"Starting to store financial data for customer: {customer_info['customer_id']}")
        db = get_db()
        customer_id = customer_info['customer_id']
        
        # Check for duplicate SMS if sms_id is provided
        if sms_id:
            logger.info(f"Checking for duplicate SMS: {sms_id}")
            is_duplicate = await check_duplicate_sms(sms_id, customer_id)
            if is_duplicate:
                logger.info(f"Duplicate SMS detected - smsId: {sms_id}, customer: {customer_id}")
                return None  # Skip processing duplicate
        
        # Get or create customer (this handles both existing and new customers)
        logger.info(f"Getting or creating customer: {customer_id}")
        customer_data = await get_or_create_customer(
            customer_id=customer_id,
            customer_name=customer_info.get('customer_name'),
            phone_number=customer_info.get('phone_number')
        )
        logger.info(f"Customer data obtained: {customer_data}")

        # Convert transaction_date to datetime object if it's a string
        if 'transaction_date' in data and data['transaction_date']:
            if isinstance(data['transaction_date'], str):
                try:
                    data['transaction_date'] = datetime.strptime(data['transaction_date'], '%Y-%m-%d')
                    logger.debug(f"Converted transaction_date to datetime: {data['transaction_date']}")
                except ValueError as e:
                    logger.warning(f"Failed to convert transaction_date {data['transaction_date']}: {str(e)}")
                    data['transaction_date'] = None

        # Get fresh database connection for storing raw message
        db = get_db()
        raw_messages = db['raw_messages']
        
        # Prepare raw message document
        raw_message_doc = {
            'customer_id': customer_id,
            'message_text': raw_message,
            'message_type': message_type,
            'important_points': important_points,
            'from': from_field,
            'sms_id': sms_id,
            'processed': True,
            'created_at': datetime.utcnow()
        }
        
        logger.info(f"Inserting raw message document: {raw_message_doc}")
        
        # Insert raw message
        try:
            raw_message_result = raw_messages.insert_one(raw_message_doc)
            raw_message_id = raw_message_result.inserted_id
            logger.info(f"Raw message stored successfully with ID: {raw_message_id}, smsId: {sms_id}")
        except Exception as e:
            logger.error(f"Failed to insert raw message: {str(e)}")
            logger.error(f"Raw message document was: {raw_message_doc}")
            raise

        # For promotional messages, only store in raw_messages
        if message_type == "PROMOTIONAL":
            logger.info("Promotional message - stored in raw_messages only")
            return str(raw_message_id)

        # Store transaction data
        transaction_doc = {
            'customer_id': customer_id,
            'message_type': message_type,
            'raw_message_id': raw_message_id,
            'sms_id': sms_id,
            'created_at': datetime.utcnow(),
            **data  # Spread the extracted data
        }

        logger.info(f"Inserting transaction document: {transaction_doc}")
        
        try:
            transactions = db['transactions']
            transaction_result = transactions.insert_one(transaction_doc)
            logger.info(f"Transaction stored successfully with ID: {transaction_result.inserted_id}")
        except Exception as e:
            logger.error(f"Failed to insert transaction: {str(e)}")
            logger.error(f"Transaction document was: {transaction_doc}")
            raise

        return str(raw_message_id)

    except Exception as e:
        logger.error(f"MongoDB storage error: {str(e)}")
        logger.error(f"Error details - message_type: {message_type}, customer_id: {customer_info.get('customer_id')}")
        raise
    finally:
        if db is not None and hasattr(db, 'client'):
            try:
                db.client.close()
            except:
                pass

async def process_single_message(
    date: Optional[str],
    message: str,
    customer_info: Optional[Dict[str, Any]] = None,
    from_field: Optional[str] = None,
    sms_id: Optional[str] = None
):
    """Process a single message with improved error handling - No regex fallback"""
    try:
        if not message or not message.strip():
            raise ValueError("Message is empty or blank")
        
        logger.info(f"Processing message: {message[:100]}...")
        logger.info(f"Customer info: {customer_info}")
        logger.info(f"SMS ID: {sms_id}")
        
        # Try LLM analysis - this is now the only method
        try:
            llm_result = await analyze_with_llm(message)
            logger.info(f"LLM analysis result: {llm_result}")
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            logger.error(f"Message that failed LLM processing: {message[:200]}...")
            
            # Return error response instead of falling back to regex
            return {
                "status": "failed",
                "error": "LLM_ANALYSIS_FAILED",
                "error_message": f"LLM model failed to process the message: {str(e)}",
                "sms_id": sms_id,
                "message": message[:100] + "..." if len(message) > 100 else message
            }
        
        # Validate LLM result
        if not llm_result or not llm_result.get("message_type") or not llm_result.get("extracted_data"):
            logger.error("LLM analysis returned invalid or incomplete result")
            logger.error(f"LLM result: {llm_result}")
            
            return {
                "status": "failed",
                "error": "LLM_RESULT_INVALID",
                "error_message": "LLM model returned invalid or incomplete analysis result",
                "sms_id": sms_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "llm_result": llm_result
            }
        
        # Process successful LLM result
        message_type = llm_result["message_type"]
        data = sanitize_llm_data(llm_result["extracted_data"])
        important_points = llm_result.get("important_points", [])
        logger.info(f"Successfully processed with LLM - Type: {message_type}, Data: {data}")
        
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
        
        # Store in database
        logger.info(f"About to store financial data...")
        raw_message_id = await store_financial_data(
            message_type=message_type,
            data=data,
            raw_message=message,
            customer_info=customer_info,
            important_points=important_points,
            from_field=from_field,
            sms_id=sms_id
        )
        
        if raw_message_id is None:
            # This means it was a duplicate SMS
            logger.info(f"Duplicate SMS skipped: {sms_id}")
            return {
                "status": "duplicate",
                "message": "Duplicate SMS skipped",
                "sms_id": sms_id
            }
            
        logger.info(f"Successfully stored data for customer {customer_info['customer_id']}")
        
        return {
            "message_type": message_type,
            "important_points": important_points,
            "data": data,
            "raw_message_id": raw_message_id,
            "status": "processed"
        }
        
    except Exception as e:
        logger.error(f"Error in process_single_message: {str(e)}")
        logger.error(f"Message: {message[:100]}")
        logger.error(f"Customer info: {customer_info}")
        
        # Return error response for any other exceptions
        return {
            "status": "failed",
            "error": "PROCESSING_ERROR",
            "error_message": f"Error processing message: {str(e)}",
            "sms_id": sms_id,
            "message": message[:100] + "..." if len(message) > 100 else message
        }

# Add a test function to verify database connectivity
async def test_database_connection():
    """Test database connection and collection creation"""
    db = None
    try:
        logger.info("Testing database connection...")
        db = get_db()
        
        # Test collections
        collections = db.list_collection_names()
        logger.info(f"Existing collections: {collections}")
        
        # Test inserting a simple document
        test_collection = db['test_collection']
        test_doc = {"test": "data", "timestamp": datetime.utcnow()}
        result = test_collection.insert_one(test_doc)
        logger.info(f"Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        logger.info("Test document deleted")
        
        logger.info("Database connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
    finally:
        if db is not None and hasattr(db, 'client'):
            try:
                db.client.close()
            except:
                pass