# from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
# from datetime import datetime
# from typing import Optional
# from app.models.pydantic_models import MessageResponse, UploadResponse, ProcessingStatus
# from app.services.message_processor import process_single_message
# from app.database import get_db
# from app.utils.logging_config import logger
# import csv
# import os
# import json

# router = APIRouter()
# processing_status = {
#     "total": 0,
#     "processed": 0,
#     "succeeded": 0,
#     "failed": 0,
#     "status": "idle"
# }

# @router.get("/")
# async def root():
#     """Health check endpoint"""
#     from app.services.llm_service import model
#     return {
#         "message": "Financial SMS Analyzer API",
#         "status": "running",
#         "version": "1.0.0",
#         "llm_status": "available" if model else "unavailable"
#     }

# @router.get("/health")
# async def health_check():
#     """Detailed health check"""
#     from app.services.llm_service import model
#     try:
#         db = get_db()
#         db.command('ping')
#         mongo_status = "connected"
#         db.client.close()
#     except Exception as e:
#         mongo_status = f"error: {str(e)}"
    
#     return {
#         "api": "healthy",
#         "mongodb": mongo_status,
#         "llm": "available" if model else "unavailable",
#         "timestamp": datetime.utcnow().isoformat()
#     }

# @router.post("/analyze-message", response_model=MessageResponse)
# async def analyze_message(
#     message: str = Form(...),
#     date: Optional[str] = Form(None),
#     customer_id: Optional[str] = Form(None),
#     customer_name: Optional[str] = Form(None),
#     phone_number: Optional[str] = Form(None)
# ):
#     """Analyze a single SMS message"""
#     try:
#         if not message or not message.strip():
#             raise HTTPException(status_code=400, detail="Message cannot be empty")
        
#         customer_info = None
#         if customer_id and customer_name and phone_number:
#             customer_info = {
#                 'customer_id': customer_id,
#                 'customer_name': customer_name,
#                 'phone_number': phone_number
#             }
        
#         result = await process_single_message(date, message, customer_info)
        
#         return MessageResponse(**result)
        
#     except ValueError as e:
#         logger.error(f"Validation error: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Message analysis error: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.post("/upload-csv", response_model=UploadResponse)
# async def upload_csv(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...),
#     delimiter: str = Form(","),
#     has_header: bool = Form(True)
# ):
#     """Upload and process CSV file containing SMS messages"""
#     try:
#         if not file.filename.endswith('.csv'):
#             raise HTTPException(status_code=400, detail="File must be a CSV file")
        
#         temp_file_path = f"temp_{file.filename}"
#         with open(temp_file_path, "wb") as buffer:
#             content = await file.read()
#             buffer.write(content)
        
#         background_tasks.add_task(
#             process_csv_file, 
#             temp_file_path, 
#             delimiter, 
#             has_header
#         )
        
#         return UploadResponse(
#             status="accepted",
#             message="CSV file uploaded successfully. Processing started in background."
#         )
        
#     except Exception as e:
#         logger.error(f"CSV upload error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# async def process_csv_file(file_path: str, delimiter: str, has_header: bool):
#     """Background task to process CSV file"""
#     global processing_status
    
#     try:
#         processing_status["status"] = "processing"
#         processing_status["processed"] = 0
#         processing_status["succeeded"] = 0
#         processing_status["failed"] = 0
        
#         logger.info(f"Starting CSV processing: {file_path}")
        
#         with open(file_path, 'r', encoding='utf-8-sig') as file:
#             csv_reader = csv.DictReader(file, delimiter=delimiter)
            
#             if not has_header:
#                 fieldnames = ['date', 'message', 'customer_id', 'customer_name', 'phone_number']
#                 file.seek(0)
#                 csv_reader = csv.DictReader(file, fieldnames=fieldnames, delimiter=delimiter)
            
#             logger.info(f"CSV headers: {csv_reader.fieldnames}")
            
#             rows = list(csv_reader)
#             processing_status["total"] = len(rows)
            
#             logger.info(f"Found {len(rows)} rows to process")
            
#             for i, row in enumerate(rows):
#                 try:
#                     logger.debug(f"Row {i+1}: {row}")
                    
#                     message = None
#                     for key in row:
#                         if key and key.lower() in ['message', 'body']:
#                             message = row[key].strip()
#                             break
                    
#                     if not message:
#                         logger.warning(f"Row {i+1}: Empty or missing message/body, skipping")
#                         processing_status["failed"] += 1
#                         continue
                    
#                     date_str = None
#                     for key in row:
#                         if key and key.lower() in ['date', 'time']:
#                             date_str = row[key].strip()
#                             break
                    
#                     customer_id = row.get('customer_id', '').strip()
#                     customer_name = row.get('customer_name', '').strip()
#                     phone_number = str(row.get('phone_number', '')).strip()
                    
#                     customer_info = None
#                     if customer_id and customer_name and phone_number:
#                         customer_info = {
#                             'customer_id': customer_id,
#                             'customer_name': customer_name,
#                             'phone_number': phone_number
#                         }
#                     elif customer_id:
#                         customer_info = {
#                             'customer_id': customer_id,
#                             'customer_name': customer_name or customer_id,
#                             'phone_number': phone_number or 'unknown'
#                         }
#                     else:
#                         logger.warning(f"Row {i+1}: Missing customer_id, skipping")
#                         processing_status["failed"] += 1
#                         continue
                    
#                     await process_single_message(date_str, message, customer_info)
#                     processing_status["succeeded"] += 1
#                     logger.info(f"Processed row {i+1}/{len(rows)}")
                    
#                 except Exception as e:
#                     logger.error(f"Error processing row {i+1}: {str(e)}")
#                     processing_status["failed"] += 1
                
#                 processing_status["processed"] += 1
            
#             processing_status["status"] = "completed"
#             logger.info(f"CSV processing completed. Success: {processing_status['succeeded']}, Failed: {processing_status['failed']}")
            
#     except Exception as e:
#         Dedent:1
#         logger.error(f"CSV processing error: {e}")
#         processing_status["status"] = "error"
    
#     finally:
#         try:
#             os.remove(file_path)
#             logger.info(f"Temporary file {file_path} removed")
#         except Exception as e:
#             logger.warning(f"Could not remove temporary file {file_path}: {str(e)}")

# @router.get("/processing-status", response_model=ProcessingStatus)
# async def get_processing_status():
#     """Get current processing status"""
#     return ProcessingStatus(**processing_status)

# @router.get("/customers")
# async def get_customers(skip: int = 0, limit: int = 100):
#     """Get list of customers"""
#     try:
#         db = get_db()
#         customers = db['customers']
        
#         cursor = customers.find({}).skip(skip).limit(limit).sort("created_at", -1)
#         customers_list = []
        
#         for customer in cursor:
#             customer['_id'] = str(customer['_id'])
#             if 'created_at' in customer:
#                 customer['created_at'] = customer['created_at'].isoformat()
#             if 'updated_at' in customer:
#                 customer['updated_at'] = customer['updated_at'].isoformat()
#             customers_list.append(customer)
        
#         total_count = customers.count_documents({})
        
#         db.client.close()
        
#         return {
#             "customers": customers_list,
#             "total": total_count,
#             "skip": skip,
#             "limit": limit
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching customers: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/customers/{customer_id}/transactions")
# async def get_customer_transactions(
#     customer_id: str, 
#     skip: int = 0, 
#     limit: int = 50,
#     message_type: Optional[str] = None
# ):
#     """Get transactions for a specific customer"""
#     try:
#         db = get_db()
#         transactions = db['transactions']
        
#         query = {"customer_id": customer_id}
#         if message_type:
#             query["message_type message_type"]
        
#         cursor = transactions.find(query).skip(skip).limit(limit).sort("created_at", -1)
#         transactions_list = []
        
#         for transaction in cursor:
#             transaction['_id'] = str(transaction['_id'])
#             if 'raw_message_id' in transaction:
#                 transaction['raw_message_id'] = str(transaction['raw_message_id'])
#             if 'created_at' in transaction:
#                 transaction['created_at'] = transaction['created_at'].isoformat()
#             if 'transaction_date' in transaction and transaction['transaction_date']:
#                 if isinstance(transaction['transaction_date'], datetime):
#                     transaction['transaction_date'] = transaction['transaction_date'].isoformat()
#             transactions_list.append(transaction)
        
#         total_count = transactions.count_documents(query)
        
#         db.client.close()
        
#         return {
#             "transactions": transactions_list,
#             "total": total_count,
#             "skip": skip,
#             "limit": limit,
#             "customer_id": customer_id
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching transactions: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/customers/{customer_id}/summary")
# async def get_customer_summary(customer_id: str):
#     """Get transaction summary for a specific customer"""
#     db = None
#     try:
#         db = get_db()
#         transactions = db['transactions']
        
#         pipeline = [
#             {"$match": {"customer_id": customer_id}},
#             {
#                 "$group": {
#                     "_id": "$message_type",
#                     "count": {"$sum": 1},
#                     "total_amount": {"$sum": "$amount"},
#                     "unique_loans": {"$addToSet": "$loan_reference"},
#                     "unique_folios": {"$addToSet": "$folio_number"},
#                     "unique_policies": {"$addToSet": "$policy_number"},
#                     "max_outstanding": {"$max": "$total_outstanding"}
#                 }
#             },
#             {
#                 "$project": {
#                     "message_type": "$_id",
#                     "count": 1,
#                     "total_amount": {"$ifNull": ["$total_amount", 0]},
#                     "unique_loans": {"$size": {"$ifNull": ["$unique_loans", []]}},
#                     "unique_folios": {"$size": {"$ifNull": ["$unique_folios", []]}},
#                     "unique_policies": {"$size": {"$ifNull": ["$unique_policies", []]}},
#                     "max_outstanding": {"$ifNull": ["$max_outstanding", 0]},
#                     "_id": 0
#                 }
#             },
#             {"$sort": {"count": -1}}
#         ]
#         message_type_stats = list(transactions.aggregate(pipeline))
        
#         total_transactions = transactions.count_documents({"customer_id": customer_id})
        
#         customers = db['customers']
#         customer = customers.find_one({"customer_id": customer_id}, {"_id": 0})
#         if not customer:
#             raise HTTPException(status_code=404, detail="Customer not found")
#         if 'created_at' in customer:
#             customer['created_at'] = customer['created_at'].isoformat()
#         if 'updated_at' in customer:
#             customer['updated_at'] = customer['updated_at'].isoformat()
        
#         return {
#             "customer": customer,
#             "total_transactions": total_transactions,
#             "message_type_stats": message_type_stats
#         }
        
#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         logger.error(f"Error fetching customer summary: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# @router.get("/customers/{customer_id}/messages")
# async def get_customer_messages(
#     customer_id: str, 
#     skip: int = 0, 
#     limit: int = 50
# ):
#     """Get raw messages for a specific customer"""
#     try:
#         db = get_db()
#         raw_messages = db['raw_messages']
        
#         cursor = raw_messages.find({"customer_id": customer_id}).skip(skip).limit(limit).sort("created_at", -1)
#         messages_list = []
        
#         for message in cursor:
#             message['_id'] = str(message['_id'])
#             if 'created_at' in message:
#                 message['created_at'] = message['created_at'].isoformat()
#             messages_list.append(message)
        
#         total_count = raw_messages.count_documents({"customer_id": customer_id})
        
#         db.client.close()
        
#         return {
#             "messages": messages_list,
#             "total": total_count,
#             "skip": skip,
#             "limit": limit,
#             "customer_id": customer_id
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching messages: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/analytics/summary")
# async def get_analytics_summary():
#     """Get analytics summary including total transactions, investments, and insurance stats"""
#     db = None
#     try:
#         db = get_db()
        
#         customers_count = db['customers'].count_documents({})
        
#         transactions = db['transactions']
#         total_transactions = transactions.count_documents({})
        
#         stats_pipeline = [
#             {
#                 "$group": {
#                     "_id": "$message_type",
#                     "count": {"$sum": 1},
#                     "total_amount": {"$sum": "$amount"},
#                     "unique_loans": {"$addToSet": "$loan_reference"},
#                     "unique_folios": {"$addToSet": "$folio_number"},
#                     "unique_policies": {"$addToSet": "$policy_number"},
#                     "max_outstanding": {"$max": "$total_outstanding"}
#                 }
#             },
#             {
#                 "$project": {
#                     "message_type": "$_id",
#                     "count": 1,
#                     "total_amount": {"$ifNull": ["$total_amount", 0]},
#                     "unique_loans": {"$size": {"$ifNull": ["$unique_loans", []]}},
#                     "unique_folios": {"$size": {"$ifNull": ["$unique_folios", []]}},
#                     "unique_policies": {"$size": {"$ifNull": ["$unique_policies", []]}},
#                     "max_outstanding": {"$ifNull": ["$max_outstanding", 0]},
#                     "_id": 0
#                 }
#             },
#             {"$sort": {"count": -1}}
#         ]
#         message_type_stats = list(transactions.aggregate(stats_pipeline))
        
#         recent_transactions = list(
#             transactions.find(
#                 {},
#                 {
#                     "message_type": 1,
#                     "amount": 1,
#                     "created_at": 1,
#                     "customer_id": 1,
#                     "loan_reference": 1,
#                     "folio_number": 1,
#                     "policy_number": 1,
#                     "total_outstanding": 1,
#                     "_id": 0
#                 }
#             )
#             .sort("created_at", -1)
#             .limit(10)
#         )
        
#         for transaction in recent_transactions:
#             if 'created_at' in transaction:
#                 transaction['created_at'] = transaction['created_at'].isoformat()
        
#         return {
#             "total_customers": customers_count,
#             "total_transactions": total_transactions,
#             "message_type_stats": message_type_stats,
#             "recent_transactions": recent_transactions
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching analytics: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# @router.get("/message-type-counts")
# async def get_message_type_counts():
#     try:
#         db = get_db()
#         pipeline = [
#             {"$group": {"_id": "$message_type", "count": {"$sum": 1}}},
#             {"$project": {"message_type": "$_id", "count": 1, "_id": 0}}
#         ]
#         results = list(db['raw_messages'].aggregate(pipeline))
#         counts = {item['message_type']: item['count'] for item in results}
#         return {"counts": counts}
#     except Exception as e:
#         logger.error(f"Error fetching message type counts: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# @router.get("/messages")
# async def get_messages_by_type(message_type: str, limit: int = 10):
#     try:
#         db = get_db()
#         raw_messages = db['raw_messages']
        
#         if message_type == "PROMOTIONAL":
#             pipeline = [
#                 {"$match": {"message_type": "PROMOTIONAL"}},
#                 {
#                     "$project": {
#                         "message": "$message_text",
#                         "important_points": "$important_points",
#                         "_id": 0
#                     }
#                 },
#                 {"$limit": limit}
#             ]
#             messages = list(raw_messages.aggregate(pipeline))
#             return messages
        
#         transactions = db['transactions']
#         pipeline = [
#             {"$match": {"message_type": message_type}},
#             {
#                 "$lookup": {
#                     "from": "raw_messages",
#                     "localField": "raw_message_id",
#                     "foreignField": "_id",
#                     "as": "raw_message"
#                 }
#             },
#             {"$unwind": "$raw_message"},
#             {
#                 "$project": {
#                     "message": "$raw_message.message_text",
#                     "extracted_data": {
#                         "amount": "$amount",
#                         "transaction_date": "$transaction_date",
#                         "account_number": "$account_number",
#                         "url": "$url"
#                     },
#                     "_id": 0
#                 }
#             },
#             {"$limit": limit}
#         ]
#         messages = list(transactions.aggregate(pipeline))
#         for msg in messages:
#             if msg['extracted_data'].get('transaction_date'):
#                 if isinstance(msg['extracted_data']['transaction_date'], datetime):
#                     msg['extracted_data']['transaction_date'] = msg['extracted_data']['transaction_date'].strftime('%Y-%m-%d')
#         return messages
#     except Exception as e:
#         logger.error(f"Error fetching messages by type {message_type}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()



# @router.post("/upload-json", response_model=UploadResponse)
# async def upload_json(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ):
#     """Upload and process JSON file containing SMS messages"""
#     try:
#         if not file.filename.endswith('.json'):
#             raise HTTPException(status_code=400, detail="File must be a JSON file")
        
#         temp_file_path = f"temp_{file.filename}"
#         with open(temp_file_path, "wb") as buffer:
#             content = await file.read()
#             buffer.write(content)
        
#         background_tasks.add_task(
#             process_json_file, 
#             temp_file_path
#         )
        
#         return UploadResponse(
#             status="accepted",
#             message="JSON file uploaded successfully. Processing started in background."
#         )
        
#     except Exception as e:
#         logger.error(f"JSON upload error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# async def process_json_file(file_path: str):
#     """Background task to process JSON file"""
#     global processing_status
    
#     try:
#         processing_status["status"] = "processing"
#         processing_status["processed"] = 0
#         processing_status["succeeded"] = 0
#         processing_status["failed"] = 0
        
#         logger.info(f"Starting JSON processing: {file_path}")
        
#         with open(file_path, 'r', encoding='utf-8') as file:
#             data = json.load(file)
            
#             if not isinstance(data, list):
#                 logger.error("JSON file must contain an array of objects")
#                 processing_status["status"] = "error"
#                 return
            
#             processing_status["total"] = len(data)
#             logger.info(f"Found {len(data)} records to process")
            
#             for i, record in enumerate(data):
#                 try:
#                     logger.debug(f"Record {i+1}: {record}")
                    
#                     # Validate record is a dictionary
#                     if not isinstance(record, dict):
#                         logger.warning(f"Record {i+1}: Not a valid object, skipping")
#                         processing_status["failed"] += 1
#                         continue
                    
#                     # Extract message field
#                     message = None
#                     for key in record:
#                         if key.lower() in ['message', 'body']:
#                             message = record[key].strip() if isinstance(record[key], str) else None
#                             break
                    
#                     if not message:
#                         logger.warning(f"Record {i+1}: Empty or missing message/body, skipping")
#                         processing_status["failed"] += 1
#                         continue
                    
#                     # Extract date field
#                     date_str = None
#                     for key in record:
#                         if key.lower() in ['date', 'time']:
#                             date_str = record[key].strip() if isinstance(record[key], str) else None
#                             break
                    
#                     # Extract customer info
#                     customer_id = record.get('customer_id', '').strip() if isinstance(record.get('customer_id'), str) else None
#                     customer_name = record.get('customer_name', '').strip() if isinstance(record.get('customer_name'), str) else None
#                     phone_number = str(record.get('phone_number', '')).strip() if record.get('phone_number') is not None else None
                    
#                     customer_info = None
#                     if customer_id and customer_name and phone_number:
#                         customer_info = {
#                             'customer_id': customer_id,
#                             'customer_name': customer_name,
#                             'phone_number': phone_number
#                         }
#                     elif customer_id:
#                         customer_info = {
#                             'customer_id': customer_id,
#                             'customer_name': customer_name or customer_id,
#                             'phone_number': phone_number or 'unknown'
#                         }
#                     else:
#                         logger.warning(f"Record {i+1}: Missing customer_id, skipping")
#                         processing_status["failed"] += 1
#                         continue
                    
#                     await process_single_message(date_str, message, customer_info)
#                     processing_status["succeeded"] += 1
#                     logger.info(f"Processed record {i+1}/{len(data)}")
                    
#                 except Exception as e:
#                     logger.error(f"Error processing record {i+1}: {str(e)}")
#                     processing_status["failed"] += 1
                
#                 processing_status["processed"] += 1
            
#             processing_status["status"] = "completed"
#             logger.info(f"JSON processing completed. Success: {processing_status['succeeded']}, Failed: {processing_status['failed']}")
            
#     except json.JSONDecodeError as e:
#         logger.error(f"Invalid JSON file: {e}")
#         processing_status["status"] = "error"
#     except Exception as e:
#         logger.error(f"JSON processing error: {e}")
#         processing_status["status"] = "error"
    
#     finally:
#         try:
#             os.remove(file_path)
#             logger.info(f"Temporary file {file_path} removed")
#         except Exception as e:
#             logger.warning(f"Could not remove temporary file {file_path}: {str(e)}")










#############################working one

# from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
# from datetime import datetime
# from typing import Optional
# from app.models.pydantic_models import MessageResponse, UploadResponse, ProcessingStatus
# from app.services.message_processor import process_single_message
# from app.database import get_db
# from app.utils.logging_config import logger
# import json
# import os
# import random

# router = APIRouter()
# processing_status = {
#     "total": 0,
#     "processed": 0,
#     "succeeded": 0,
#     "failed": 0,
#     "status": "idle"
# }

# # Hardcoded users
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

# @router.get("/")
# async def root():
#     """Health check endpoint"""
#     from app.services.llm_service import model
#     return {
#         "message": "Financial SMS Analyzer API",
#         "status": "running",
#         "version": "1.0.0",
#         "llm_status": "available" if model else "unavailable"
#     }

# @router.get("/health")
# async def health_check():
#     """Detailed health check"""
#     from app.services.llm_service import model
#     try:
#         db = get_db()
#         db.command('ping')
#         mongo_status = "connected"
#         db.client.close()
#     except Exception as e:
#         mongo_status = f"error: {str(e)}"
    
#     return {
#         "api": "healthy",
#         "mongodb": mongo_status,
#         "llm": "available" if model else "unavailable",
#         "timestamp": datetime.utcnow().isoformat()
#     }

# @router.post("/analyze-message", response_model=MessageResponse)
# async def analyze_message(
#     message: str = Form(...),
#     date: Optional[str] = Form(None),
#     customer_id: Optional[str] = Form(None),
#     customer_name: Optional[str] = Form(None),
#     phone_number: Optional[str] = Form(None)
# ):
#     """Analyze a single SMS message"""
#     try:
#         if not message or not message.strip():
#             raise HTTPException(status_code=400, detail="Message cannot be empty")
        
#         customer_info = None
#         if customer_id and customer_name and phone_number:
#             customer_info = {
#                 'customer_id': customer_id,
#                 'customer_name': customer_name,
#                 'phone_number': phone_number
#             }
        
#         result = await process_single_message(date, message, customer_info)
        
#         return MessageResponse(**result)
        
#     except ValueError as e:
#         logger.error(f"Validation error: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Message analysis error: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.post("/upload-json", response_model=UploadResponse)
# async def upload_json(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...)
# ):
#     """Upload and process JSON file containing SMS messages"""
#     try:
#         if not file.filename.endswith('.json'):
#             raise HTTPException(status_code=400, detail="File must be a JSON file")
        
#         temp_file_path = f"temp_{file.filename}"
#         with open(temp_file_path, "wb") as buffer:
#             content = await file.read()
#             buffer.write(content)
        
#         background_tasks.add_task(
#             process_json_file, 
#             temp_file_path
#         )
        
#         return UploadResponse(
#             status="accepted",
#             message="JSON file uploaded successfully. Processing started in background."
#         )
        
#     except Exception as e:
#         logger.error(f"JSON upload error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# async def process_json_file(file_path: str):
#     """Background task to process JSON file"""
#     global processing_status
    
#     try:
#         processing_status["status"] = "processing"
#         processing_status["processed"] = 0
#         processing_status["succeeded"] = 0
#         processing_status["failed"] = 0
        
#         logger.info(f"Starting JSON processing: {file_path}")
        
#         with open(file_path, 'r', encoding='utf-8') as file:
#             data = json.load(file)
            
#             if not isinstance(data, list):
#                 logger.error("JSON file must contain an array of objects")
#                 processing_status["status"] = "error"
#                 return
            
#             processing_status["total"] = len(data)
#             logger.info(f"Found {len(data)} records to process")
            
#             for i, record in enumerate(data):
#                 try:
#                     logger.debug(f"Processing record {i+1}: {record}")
                    
#                     # Validate record is a dictionary
#                     if not isinstance(record, dict):
#                         logger.warning(f"Record {i+1}: Not a valid object, skipping")
#                         processing_status["failed"] += 1
#                         continue
                    
#                     # Extract message field (try 'message', 'body', or similar)
#                     message = None
#                     message_field = None
#                     for key in record:
#                         if key.lower() in ['message', 'body', 'text', 'content']:
#                             if isinstance(record[key], str) and record[key].strip():
#                                 message = record[key].strip()
#                                 message_field = key
#                                 break
                    
#                     if not message:
#                         logger.warning(f"Record {i+1}: No valid message field found, skipping")
#                         processing_status["failed"] += 1
#                         continue
                    
#                     logger.debug(f"Record {i+1}: Identified message in field '{message_field}'")
                    
#                     # Extract date field (try 'date', 'time', or similar)
#                     date_str = None
#                     date_field = None
#                     for key in record:
#                         if key.lower() in ['date', 'time', 'timestamp']:
#                             if isinstance(record[key], str) and record[key].strip():
#                                 date_str = record[key].strip()
#                                 date_field = key
#                                 break
                    
#                     if date_str:
#                         logger.debug(f"Record {i+1}: Identified date in field '{date_field}'")
#                     else:
#                         logger.debug(f"Record {i+1}: No date field found")
                    
#                     # Extract customer information
#                     customer_info = None
#                     customer_id = None
#                     customer_name = None
#                     phone_number = None
                    
#                     for key in record:
#                         key_lower = key.lower()
#                         if key_lower in ['customer_id', 'customerid', 'cid']:
#                             customer_id = record[key].strip() if isinstance(record[key], str) else None
#                         elif key_lower in ['customer_name', 'customername', 'name']:
#                             customer_name = record[key].strip() if isinstance(record[key], str) else None
#                         elif key_lower in ['phone_number', 'phonenumber', 'phone', 'mobile']:
#                             phone_number = record[key].strip() if isinstance(record[key], str) else None
                    
#                     if customer_id and customer_name and phone_number:
#                         customer_info = {
#                             'customer_id': customer_id,
#                             'customer_name': customer_name,
#                             'phone_number': phone_number
#                         }
#                         logger.debug(f"Record {i+1}: Using provided customer info: {customer_info}")
#                     else:
#                         customer_info = random.choice(HARDCODED_USERS)
#                         logger.debug(f"Record {i+1}: Assigned random user: {customer_info['customer_id']}")
                    
#                     # Process the message
#                     await process_single_message(date_str, message, customer_info)
#                     processing_status["succeeded"] += 1
#                     logger.info(f"Successfully processed record {i+1}/{len(data)}")
                    
#                 except Exception as e:
#                     logger.error(f"Error processing record {i+1}: {str(e)}")
#                     processing_status["failed"] += 1
                
#                 processing_status["processed"] += 1
            
#             processing_status["status"] = "completed"
#             logger.info(f"JSON processing completed. Success: {processing_status['succeeded']}, Failed: {processing_status['failed']}")
            
#     except json.JSONDecodeError as e:
#         logger.error(f"Invalid JSON file: {e}")
#         processing_status["status"] = "error"
#     except Exception as e:
#         logger.error(f"JSON processing error: {e}")
#         processing_status["status"] = "error"
    
#     finally:
#         try:
#             os.remove(file_path)
#             logger.info(f"Temporary file {file_path} removed")
#         except Exception as e:
#             logger.warning(f"Could not remove temporary file {file_path}: {str(e)}")

# @router.get("/processing-status", response_model=ProcessingStatus)
# async def get_processing_status():
#     """Get current processing status"""
#     return ProcessingStatus(**processing_status)

# @router.get("/customers")
# async def get_customers(skip: int = 0, limit: int = 100):
#     """Get list of customers"""
#     try:
#         db = get_db()
#         customers = db['customers']
        
#         cursor = customers.find({}).skip(skip).limit(limit).sort("created_at", -1)
#         customers_list = []
        
#         for customer in cursor:
#             customer['_id'] = str(customer['_id'])
#             if 'created_at' in customer:
#                 customer['created_at'] = customer['created_at'].isoformat()
#             if 'updated_at' in customer:
#                 customer['updated_at'] = customer['updated_at'].isoformat()
#             customers_list.append(customer)
        
#         total_count = customers.count_documents({})
        
#         db.client.close()
        
#         return {
#             "customers": customers_list,
#             "total": total_count,
#             "skip": skip,
#             "limit": limit
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching customers: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/customers/{customer_id}/transactions")
# async def get_customer_transactions(
#     customer_id: str, 
#     skip: int = 0, 
#     limit: int = 50,
#     message_type: Optional[str] = None
# ):
#     """Get transactions for a specific customer"""
#     try:
#         db = get_db()
#         transactions = db['transactions']
        
#         query = {"customer_id": customer_id}
#         if message_type:
#             query["message_type"] = message_type
        
#         cursor = transactions.find(query).skip(skip).limit(limit).sort("created_at", -1)
#         transactions_list = []
        
#         for transaction in cursor:
#             transaction['_id'] = str(transaction['_id'])
#             if 'raw_message_id' in transaction:
#                 transaction['raw_message_id'] = str(transaction['raw_message_id'])
#             if 'created_at' in transaction:
#                 transaction['created_at'] = transaction['created_at'].isoformat()
#             if 'transaction_date' in transaction and transaction['transaction_date']:
#                 if isinstance(transaction['transaction_date'], datetime):
#                     transaction['transaction_date'] = transaction['transaction_date'].isoformat()
#             transactions_list.append(transaction)
        
#         total_count = transactions.count_documents(query)
        
#         db.client.close()
        
#         return {
#             "transactions": transactions_list,
#             "total": total_count,
#             "skip": skip,
#             "limit": limit,
#             "customer_id": customer_id
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching transactions: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/customers/{customer_id}/summary")
# async def get_customer_summary(customer_id: str):
#     """Get transaction summary for a specific customer"""
#     db = None
#     try:
#         db = get_db()
#         transactions = db['transactions']
        
#         pipeline = [
#             {"$match": {"customer_id": customer_id}},
#             {
#                 "$group": {
#                     "_id": "$message_type",
#                     "count": {"$sum": 1},
#                     "total_amount": {"$sum": "$amount"},
#                     "unique_loans": {"$addToSet": "$loan_reference"},
#                     "unique_folios": {"$addToSet": "$folio_number"},
#                     "unique_policies": {"$addToSet": "$policy_number"},
#                     "max_outstanding": {"$max": "$total_outstanding"}
#                 }
#             },
#             {
#                 "$project": {
#                     "message_type": "$_id",
#                     "count": 1,
#                     "total_amount": {"$ifNull": ["$total_amount", 0]},
#                     "unique_loans": {"$size": {"$ifNull": ["$unique_loans", []]}},
#                     "unique_folios": {"$size": {"$ifNull": ["$unique_folios", []]}},
#                     "unique_policies": {"$size": {"$ifNull": ["$unique_policies", []]}},
#                     "max_outstanding": {"$ifNull": ["$max_outstanding", 0]},
#                     "_id": 0
#                 }
#             },
#             {"$sort": {"count": -1}}
#         ]
#         message_type_stats = list(transactions.aggregate(pipeline))
        
#         total_transactions = transactions.count_documents({"customer_id": customer_id})
        
#         customers = db['customers']
#         customer = customers.find_one({"customer_id": customer_id}, {"_id": 0})
#         if not customer:
#             raise HTTPException(status_code=404, detail="Customer not found")
#         if 'created_at' in customer:
#             customer['created_at'] = customer['created_at'].isoformat()
#         if 'updated_at' in customer:
#             customer['updated_at'] = customer['updated_at'].isoformat()
        
#         return {
#             "customer": customer,
#             "total_transactions": total_transactions,
#             "message_type_stats": message_type_stats
#         }
        
#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         logger.error(f"Error fetching customer summary: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# @router.get("/customers/{customer_id}/messages")
# async def get_customer_messages(
#     customer_id: str, 
#     skip: int = 0, 
#     limit: int = 50
# ):
#     """Get raw messages for a specific customer"""
#     try:
#         db = get_db()
#         raw_messages = db['raw_messages']
        
#         cursor = raw_messages.find({"customer_id": customer_id}).skip(skip).limit(limit).sort("created_at", -1)
#         messages_list = []
        
#         for message in cursor:
#             message['_id'] = str(message['_id'])
#             if 'created_at' in message:
#                 message['created_at'] = message['created_at'].isoformat()
#             messages_list.append(message)
        
#         total_count = raw_messages.count_documents({"customer_id": customer_id})
        
#         db.client.close()
        
#         return {
#             "messages": messages_list,
#             "total": total_count,
#             "skip": skip,
#             "limit": limit,
#             "customer_id": customer_id
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching messages: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/analytics/summary")
# async def get_analytics_summary():
#     """Get analytics summary including total transactions, investments, and insurance stats"""
#     db = None
#     try:
#         db = get_db()
        
#         customers_count = db['customers'].count_documents({})
        
#         transactions = db['transactions']
#         total_transactions = transactions.count_documents({})
        
#         stats_pipeline = [
#             {
#                 "$group": {
#                     "_id": "$message_type",
#                     "count": {"$sum": 1},
#                     "total_amount": {"$sum": "$amount"},
#                     "unique_loans": {"$addToSet": "$loan_reference"},
#                     "unique_folios": {"$addToSet": "$folio_number"},
#                     "unique_policies": {"$addToSet": "$policy_number"},
#                     "max_outstanding": {"$max": "$total_outstanding"}
#                 }
#             },
#             {
#                 "$project": {
#                     "message_type": "$_id",
#                     "count": 1,
#                     "total_amount": {"$ifNull": ["$total_amount", 0]},
#                     "unique_loans": {"$size": {"$ifNull": ["$unique_loans", []]}},
#                     "unique_folios": {"$size": {"$ifNull": ["$unique_folios", []]}},
#                     "unique_policies": {"$size": {"$ifNull": ["$unique_policies", []]}},
#                     "max_outstanding": {"$ifNull": ["$max_outstanding", 0]},
#                     "_id": 0
#                 }
#             },
#             {"$sort": {"count": -1}}
#         ]
#         message_type_stats = list(transactions.aggregate(stats_pipeline))
        
#         recent_transactions = list(
#             transactions.find(
#                 {},
#                 {
#                     "message_type": 1,
#                     "amount": 1,
#                     "created_at": 1,
#                     "customer_id": 1,
#                     "loan_reference": 1,
#                     "folio_number": 1,
#                     "policy_number": 1,
#                     "total_outstanding": 1,
#                     "_id": 0
#                 }
#             )
#             .sort("created_at", -1)
#             .limit(10)
#         )
        
#         for transaction in recent_transactions:
#             if 'created_at' in transaction:
#                 transaction['created_at'] = transaction['created_at'].isoformat()
        
#         return {
#             "total_customers": customers_count,
#             "total_transactions": total_transactions,
#             "message_type_stats": message_type_stats,
#             "recent_transactions": recent_transactions
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching analytics: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# @router.get("/message-type-counts")
# async def get_message_type_counts():
#     try:
#         db = get_db()
#         pipeline = [
#             {"$group": {"_id": "$message_type", "count": {"$sum": 1}}},
#             {"$project": {"message_type": "$_id", "count": 1, "_id": 0}}
#         ]
#         results = list(db['raw_messages'].aggregate(pipeline))
#         counts = {item['message_type']: item['count'] for item in results}
#         return {"counts": counts}
#     except Exception as e:
#         logger.error(f"Error fetching message type counts: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# @router.get("/messages")
# async def get_messages_by_type(message_type: str, limit: int = 10):
#     try:
#         db = get_db()
#         raw_messages = db['raw_messages']
        
#         if message_type == "PROMOTIONAL":
#             pipeline = [
#                 {"$match": {"message_type": "PROMOTIONAL"}},
#                 {
#                     "$project": {
#                         "message": "$message_text",
#                         "important_points": "$important_points",
#                         "_id": 0
#                     }
#                 },
#                 {"$limit": limit}
#             ]
#             messages = list(raw_messages.aggregate(pipeline))
#             return messages
        
#         transactions = db['transactions']
#         pipeline = [
#             {"$match": {"message_type": message_type}},
#             {
#                 "$lookup": {
#                     "from": "raw_messages",
#                     "localField": "raw_message_id",
#                     "foreignField": "_id",
#                     "as": "raw_message"
#                 }
#             },
#             {"$unwind": "$raw_message"},
#             {
#                 "$project": {
#                     "message": "$raw_message.message_text",
#                     "extracted_data": {
#                         "amount": "$amount",
#                         "transaction_date": "$transaction_date",
#                         "account_number": "$account_number",
#                         "url": "$url"
#                     },
#                     "_id": 0
#                 }
#             },
#             {"$limit": limit}
#         ]
#         messages = list(transactions.aggregate(pipeline))
#         for msg in messages:
#             if msg['extracted_data'].get('transaction_date'):
#                 if isinstance(msg['extracted_data']['transaction_date'], datetime):
#                     msg['extracted_data']['transaction_date'] = msg['extracted_data']['transaction_date'].strftime('%Y-%m-%d')
#         return messages
#     except Exception as e:
#         logger.error(f"Error fetching messages by type {message_type}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()

# @router.get("/messages_demo")
# async def get_messages_by_type(message_type: str, limit: int = 10):
#     try:
#         db = get_db()
#         raw_messages = db['raw_messages']
        
#         if message_type == "PROMOTIONAL":
#             pipeline = [
#                 {"$match": {"message_type": "PROMOTIONAL"}},
#                 {
#                     "$project": {
#                         "message": "$message_text",
#                         "important_points": "$important_points",
#                         "_id": 0
#                     }
#                 },
#                 {"$limit": limit}
#             ]
#             messages = list(raw_messages.aggregate(pipeline))
#             return messages
        
#         transactions = db['transactions']
#         pipeline = [
#             {"$match": {"message_type": message_type}},
#             {
#                 "$lookup": {
#                     "from": "raw_messages",
#                     "localField": "raw_message_id",
#                     "foreignField": "_id",
#                     "as": "raw_message"
#                 }
#             },
#             {"$unwind": "$raw_message"},
#             {
#                 "$addFields": {
#                     "all_fields": {
#                         "$objectToArray": "$$ROOT"
#                     }
#                 }
#             },
#             {
#                 "$addFields": {
#                     "important_points_array": {
#                         "$filter": {
#                             "input": "$all_fields",
#                             "as": "field",
#                             "cond": {
#                                 "$and": [
#                                     {"$ne": ["$$field.k", "_id"]},
#                                     {"$ne": ["$$field.k", "raw_message"]},
#                                     {"$ne": ["$$field.k", "raw_message_id"]},
#                                     {"$ne": ["$$field.k", "customer_id"]},
#                                     {"$ne": ["$$field.k", "created_at"]},
#                                     {"$ne": ["$$field.k", "message_type"]}
#                                 ]
#                             }
#                         }
#                     }
#                 }
#             },
#             {
#                 "$addFields": {
#                     "important_points": {
#                         "$arrayToObject": "$important_points_array"
#                     }
#                 }
#             },
#             {
#                 "$project": {
#                     "_id": 0,
#                     "message": "$raw_message.message_text",
#                     "important_points": 1
#                 }
#             },
#             {"$limit": limit}
#         ]
#         messages = list(transactions.aggregate(pipeline))
        
#         # Handle date formatting for all messages
#         for msg in messages:
#             extracted_data = msg.get('extracted_data', {})
#             if extracted_data.get('transaction_date'):
#                 if isinstance(extracted_data['transaction_date'], datetime):
#                     extracted_data['transaction_date'] = extracted_data['transaction_date'].strftime('%Y-%m-%d')
        
#         return messages
#     except Exception as e:
#         logger.error(f"Error fetching messages by type {message_type}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db is not None and hasattr(db, 'client'):
#             db.client.close()



from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.pydantic_models import MessageResponse, UploadResponse, ProcessingStatus
from app.services.message_processor import process_single_message
from app.database import get_db
from app.utils.logging_config import logger
import json
import os
import random
import asyncio
from threading import Lock

router = APIRouter()

# Thread-safe processing status with lock
processing_lock = Lock()
processing_status: Dict[str, Any] = {
    "total": 0,
    "processed": 0,
    "succeeded": 0,
    "failed": 0,
    "status": "idle",
    "current_file": None,
    "start_time": None,
    "end_time": None,
    "error_message": None
}

# Hardcoded users
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

def update_processing_status(**kwargs):
    """Thread-safe function to update processing status"""
    with processing_lock:
        for key, value in kwargs.items():
            if key in processing_status:
                processing_status[key] = value
        logger.debug(f"Processing status updated: {processing_status}")

def get_processing_status_copy():
    """Thread-safe function to get processing status copy"""
    with processing_lock:
        return processing_status.copy()

@router.get("/")
async def root():
    """Health check endpoint"""
    from app.services.llm_service import model
    return {
        "message": "Financial SMS Analyzer API",
        "status": "running",
        "version": "1.0.0",
        "llm_status": "available" if model else "unavailable"
    }

@router.get("/health")
async def health_check():
    """Detailed health check"""
    from app.services.llm_service import model
    try:
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

@router.post("/analyze-message", response_model=MessageResponse)
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
        
        customer_info = None
        if customer_id and customer_name and phone_number:
            customer_info = {
                'customer_id': customer_id,
                'customer_name': customer_name,
                'phone_number': phone_number
            }
        
        result = await process_single_message(date, message, customer_info)
        
        return MessageResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Message analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upload-json", response_model=UploadResponse)
async def upload_json(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process JSON file containing SMS messages"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")
        
        # Check if processing is already running
        current_status = get_processing_status_copy()
        if current_status["status"] == "processing":
            raise HTTPException(
                status_code=409, 
                detail="Another file is currently being processed. Please wait for it to complete."
            )
        
        temp_file_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Reset processing status
        update_processing_status(
            total=0,
            processed=0,
            succeeded=0,
            failed=0,
            status="queued",
            current_file=file.filename,
            start_time=datetime.utcnow().isoformat(),
            end_time=None,
            error_message=None
        )
        
        background_tasks.add_task(
            process_json_file, 
            temp_file_path,
            file.filename
        )
        
        return UploadResponse(
            status="accepted",
            message="JSON file uploaded successfully. Processing started in background."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON upload error: {e}")
        update_processing_status(
            status="error",
            error_message=str(e),
            end_time=datetime.utcnow().isoformat()
        )
        raise HTTPException(status_code=500, detail=str(e))

async def process_json_file(file_path: str, original_filename: str):
    """Background task to process JSON file"""
    
    try:
        update_processing_status(
            status="processing",
            processed=0,
            succeeded=0,
            failed=0,
            current_file=original_filename,
            start_time=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Starting JSON processing: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            if not isinstance(data, list):
                error_msg = "JSON file must contain an array of objects"
                logger.error(error_msg)
                update_processing_status(
                    status="error",
                    error_message=error_msg,
                    end_time=datetime.utcnow().isoformat()
                )
                return
            
            update_processing_status(total=len(data))
            logger.info(f"Found {len(data)} records to process")
            
            for i, record in enumerate(data):
                try:
                    logger.debug(f"Processing record {i+1}: {record}")
                    
                    # Validate record is a dictionary
                    if not isinstance(record, dict):
                        logger.warning(f"Record {i+1}: Not a valid object, skipping")
                        update_processing_status(failed=get_processing_status_copy()["failed"] + 1)
                        continue
                    
                    # Extract message field (try 'message', 'body', or similar)
                    message = None
                    message_field = None
                    for key in record:
                        if key.lower() in ['message', 'body', 'text', 'content']:
                            if isinstance(record[key], str) and record[key].strip():
                                message = record[key].strip()
                                message_field = key
                                break
                    
                    if not message:
                        logger.warning(f"Record {i+1}: No valid message field found, skipping")
                        update_processing_status(failed=get_processing_status_copy()["failed"] + 1)
                        continue
                    
                    logger.debug(f"Record {i+1}: Identified message in field '{message_field}'")
                    
                    # Extract date field (try 'date', 'time', or similar)
                    date_str = None
                    date_field = None
                    for key in record:
                        if key.lower() in ['date', 'time', 'timestamp']:
                            if isinstance(record[key], str) and record[key].strip():
                                date_str = record[key].strip()
                                date_field = key
                                break
                    
                    if date_str:
                        logger.debug(f"Record {i+1}: Identified date in field '{date_field}'")
                    else:
                        logger.debug(f"Record {i+1}: No date field found")
                    
                    # Extract customer information
                    customer_info = None
                    customer_id = None
                    customer_name = None
                    phone_number = None
                    
                    for key in record:
                        key_lower = key.lower()
                        if key_lower in ['customer_id', 'customerid', 'cid']:
                            customer_id = record[key].strip() if isinstance(record[key], str) else None
                        elif key_lower in ['customer_name', 'customername', 'name']:
                            customer_name = record[key].strip() if isinstance(record[key], str) else None
                        elif key_lower in ['phone_number', 'phonenumber', 'phone', 'mobile']:
                            phone_number = record[key].strip() if isinstance(record[key], str) else None
                    
                    if customer_id and customer_name and phone_number:
                        customer_info = {
                            'customer_id': customer_id,
                            'customer_name': customer_name,
                            'phone_number': phone_number
                        }
                        logger.debug(f"Record {i+1}: Using provided customer info: {customer_info}")
                    else:
                        customer_info = random.choice(HARDCODED_USERS)
                        logger.debug(f"Record {i+1}: Assigned random user: {customer_info['customer_id']}")
                    
                    # Process the message
                    await process_single_message(date_str, message, customer_info)
                    
                    # Update success count
                    current_status = get_processing_status_copy()
                    update_processing_status(succeeded=current_status["succeeded"] + 1)
                    logger.info(f"Successfully processed record {i+1}/{len(data)}")
                    
                except Exception as e:
                    logger.error(f"Error processing record {i+1}: {str(e)}")
                    current_status = get_processing_status_copy()
                    update_processing_status(failed=current_status["failed"] + 1)
                
                # Update processed count and add small delay to allow status updates
                current_status = get_processing_status_copy()
                update_processing_status(processed=current_status["processed"] + 1)
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.01)
            
            # Mark as completed
            final_status = get_processing_status_copy()
            update_processing_status(
                status="completed",
                end_time=datetime.utcnow().isoformat()
            )
            logger.info(f"JSON processing completed. Success: {final_status['succeeded']}, Failed: {final_status['failed']}")
            
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON file: {e}"
        logger.error(error_msg)
        update_processing_status(
            status="error",
            error_message=error_msg,
            end_time=datetime.utcnow().isoformat()
        )
    except Exception as e:
        error_msg = f"JSON processing error: {e}"
        logger.error(error_msg)
        update_processing_status(
            status="error",
            error_message=error_msg,
            end_time=datetime.utcnow().isoformat()
        )
    
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file {file_path} removed")
        except Exception as e:
            logger.warning(f"Could not remove temporary file {file_path}: {str(e)}")

@router.get("/processing-status", response_model=ProcessingStatus)
async def get_processing_status():
    """Get current processing status"""
    status = get_processing_status_copy()
    
    # Add progress percentage
    if status["total"] > 0:
        status["progress_percentage"] = round((status["processed"] / status["total"]) * 100, 2)
    else:
        status["progress_percentage"] = 0.0
    
    # Add estimated time remaining if processing
    if status["status"] == "processing" and status["processed"] > 0 and status["start_time"]:
        try:
            start_time = datetime.fromisoformat(status["start_time"].replace('Z', '+00:00'))
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            avg_time_per_item = elapsed_time / status["processed"]
            remaining_items = status["total"] - status["processed"]
            estimated_remaining_seconds = remaining_items * avg_time_per_item
            status["estimated_remaining_seconds"] = round(estimated_remaining_seconds, 2)
        except Exception as e:
            logger.debug(f"Could not calculate estimated time: {e}")
            status["estimated_remaining_seconds"] = None
    else:
        status["estimated_remaining_seconds"] = None
    
    return ProcessingStatus(**status)

@router.post("/reset-processing-status")
async def reset_processing_status():
    """Reset processing status - useful for debugging or if status gets stuck"""
    update_processing_status(
        total=0,
        processed=0,
        succeeded=0,
        failed=0,
        status="idle",
        current_file=None,
        start_time=None,
        end_time=None,
        error_message=None
    )
    return {"message": "Processing status reset successfully"}

@router.get("/customers")
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

@router.get("/customers/{customer_id}/transactions")
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

@router.get("/customers/{customer_id}/summary")
async def get_customer_summary(customer_id: str):
    """Get transaction summary for a specific customer"""
    db = None
    try:
        db = get_db()
        transactions = db['transactions']
        
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
        
        total_transactions = transactions.count_documents({"customer_id": customer_id})
        
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

@router.get("/customers/{customer_id}/messages")
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

@router.get("/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary including total transactions, investments, and insurance stats"""
    db = None
    try:
        db = get_db()
        
        customers_count = db['customers'].count_documents({})
        
        transactions = db['transactions']
        total_transactions = transactions.count_documents({})
        
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

@router.get("/message-type-counts")
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

@router.get("/messages")
async def get_messages_by_type(message_type: str, limit: int = 10):
    db = None
    try:
        db = get_db()
        raw_messages = db['raw_messages']
        
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

@router.get("/messages_demo")
async def get_messages_by_type_demo(message_type: str, limit: int = 10):
    db = None
    try:
        db = get_db()
        raw_messages = db['raw_messages']
        
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
                "$addFields": {
                    "all_fields": {
                        "$objectToArray": "$$ROOT"
                    }
                }
            },
            {
                "$addFields": {
                    "important_points_array": {
                        "$filter": {
                            "input": "$all_fields",
                            "as": "field",
                            "cond": {
                                "$and": [
                                    {"$ne": ["$$field.k", "_id"]},
                                    {"$ne": ["$$field.k", "raw_message"]},
                                    {"$ne": ["$$field.k", "raw_message_id"]},
                                    {"$ne": ["$$field.k", "customer_id"]},
                                    {"$ne": ["$$field.k", "created_at"]},
                                    {"$ne": ["$$field.k", "message_type"]}
                                ]
                            }
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "important_points": {
                        "$arrayToObject": "$important_points_array"
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "message": "$raw_message.message_text",
                    "important_points": 1
                }
            },
            {"$limit": limit}
        ]
        messages = list(transactions.aggregate(pipeline))
        
        # Handle date formatting for all messages
        for msg in messages:
            extracted_data = msg.get('extracted_data', {})
            if extracted_data.get('transaction_date'):
                if isinstance(extracted_data['transaction_date'], datetime):
                    extracted_data['transaction_date'] = extracted_data['transaction_date'].strftime('%Y-%m-%d')
        
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages by type {message_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db is not None and hasattr(db, 'client'):
            db.client.close()