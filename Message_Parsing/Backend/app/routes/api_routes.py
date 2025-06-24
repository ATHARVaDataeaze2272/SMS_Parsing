############################### working

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends
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
            duplicates=0,  # Add duplicate counter
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
                    
                    if not isinstance(record, dict):
                        logger.warning(f"Record {i+1}: Not a valid object, skipping")
                        update_processing_status(failed=get_processing_status_copy()["failed"] + 1)
                        continue
                    
                    # Flexible message field extraction
                    message = None
                    for key in ['body', 'message', 'text', 'content']:
                        if key in record and isinstance(record[key], str) and record[key].strip():
                            message = record[key].strip()
                            logger.debug(f"Record {i+1}: Identified message in '{key}' field")
                            break
                    
                    if not message:
                        logger.warning(f"Record {i+1}: No valid message field found, skipping")
                        update_processing_status(failed=get_processing_status_copy()["failed"] + 1)
                        continue
                    
                    # Flexible date field extraction
                    date_str = None
                    for key in ['time', 'date', 'timestamp']:
                        if key in record and isinstance(record[key], str) and record[key].strip():
                            date_str = record[key].strip()
                            logger.debug(f"Record {i+1}: Identified date in '{key}' field: {date_str}")
                            break
                    
                    # Extract 'from' field
                    from_field = record.get('from')
                    if from_field and isinstance(from_field, str) and from_field.strip():
                        logger.debug(f"Record {i+1}: Identified 'from' field: {from_field}")
                    else:
                        from_field = None
                        logger.debug(f"Record {i+1}: No valid 'from' field found")
                    
                    # Extract SMS ID
                    sms_id = record.get('smsId')
                    if sms_id and isinstance(sms_id, str) and sms_id.strip():
                        logger.debug(f"Record {i+1}: Identified smsId: {sms_id}")
                    else:
                        sms_id = None
                        logger.debug(f"Record {i+1}: No valid smsId found")
                    
                    # Extract customer ID - FIXED: Don't use random assignment if cid exists
                    customer_id = None
                    for key in ['cid', 'customer_id', 'customerid']:
                        if key in record and isinstance(record[key], str) and record[key].strip():
                            customer_id = record[key].strip()
                            logger.debug(f"Record {i+1}: Identified customer ID in '{key}' field: {customer_id}")
                            break
                    
                    # Prepare customer info - ONLY use hardcoded users if no customer_id found
                    customer_info = None
                    if customer_id:
                        customer_info = {'customer_id': customer_id}
                        logger.debug(f"Record {i+1}: Using customer ID from JSON: {customer_id}")
                    else:
                        customer_info = random.choice(HARDCODED_USERS)
                        logger.debug(f"Record {i+1}: No customer ID found, assigned random user: {customer_info['customer_id']}")
                    
                    # Process the message
                    result = await process_single_message(
                        date=date_str,
                        message=message,
                        customer_info=customer_info,
                        from_field=from_field,
                        sms_id=sms_id
                    )
                    
                    # Update counters based on result
                    current_status = get_processing_status_copy()
                    if result.get("status") == "duplicate":
                        update_processing_status(duplicates=current_status.get("duplicates", 0) + 1)
                        logger.info(f"Duplicate SMS skipped for record {i+1}/{len(data)}")
                    else:
                        update_processing_status(succeeded=current_status["succeeded"] + 1)
                        logger.info(f"Successfully processed record {i+1}/{len(data)}")
                    
                except Exception as e:
                    logger.error(f"Error processing record {i+1}: {str(e)}")
                    current_status = get_processing_status_copy()
                    update_processing_status(failed=current_status["failed"] + 1)
                
                finally:
                    # Always update processed count
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
            logger.info(f"JSON processing completed. Success: {final_status['succeeded']}, Failed: {final_status['failed']}, Duplicates: {final_status.get('duplicates', 0)}")
            
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


@router.get("/analytics/summary-demo")
async def get_analytics_summary():
    """Get analytics summary including total transactions, investments, and insurance stats"""
    db = None
    try:
        db = get_db()
        
        customers_count = db['customers'].count_documents({})
        
        transactions = db['transactions']
        total_transactions = transactions.count_documents({})
        
        # Fixed aggregation pipeline
        stats_pipeline = [
            {
                "$group": {
                    "_id": "$message_type",
                    "count": {"$sum": 1},
                    # Only sum amount if it exists and is numeric
                    "total_amount": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$ne": ["$amount", None]},
                                        {"$ne": ["$amount", ""]},
                                        {"$type": ["$amount", "number"]}
                                    ]
                                },
                                "$amount",
                                0
                            ]
                        }
                    },
                    # Filter out null/empty values before adding to set
                    "unique_loans": {
                        "$addToSet": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$ne": ["$loan_reference", None]},
                                        {"$ne": ["$loan_reference", ""]}
                                    ]
                                },
                                "$loan_reference",
                                "$$REMOVE"
                            ]
                        }
                    },
                    "unique_folios": {
                        "$addToSet": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$ne": ["$folio_number", None]},
                                        {"$ne": ["$folio_number", ""]}
                                    ]
                                },
                                "$folio_number",
                                "$$REMOVE"
                            ]
                        }
                    },
                    "unique_policies": {
                        "$addToSet": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$ne": ["$policy_number", None]},
                                        {"$ne": ["$policy_number", ""]}
                                    ]
                                },
                                "$policy_number",
                                "$$REMOVE"
                            ]
                        }
                    },
                    "max_outstanding": {
                        "$max": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$ne": ["$total_outstanding", None]},
                                        {"$ne": ["$total_outstanding", ""]},
                                        {"$type": ["$total_outstanding", "number"]}
                                    ]
                                },
                                "$total_outstanding",
                                0
                            ]
                        }
                    }
                }
            },
            {
                "$project": {
                    "message_type": "$_id",
                    "count": 1,
                    "total_amount": 1,  # No need for $ifNull since we handled it above
                    "unique_loans": {"$size": "$unique_loans"},
                    "unique_folios": {"$size": "$unique_folios"},
                    "unique_policies": {"$size": "$unique_policies"},
                    "max_outstanding": 1,  # No need for $ifNull since we handled it above
                    "_id": 0
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        message_type_stats = list(transactions.aggregate(stats_pipeline))
        
        # Debug: Add logging to see what's in the pipeline results
        logger.info(f"Aggregation results: {message_type_stats}")
        
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


# Alternative simpler approach if the above is too complex
@router.get("/analytics/summary")
async def get_analytics_summary_simple():
    """Simplified analytics summary with better error handling"""
    db = None
    try:
        db = get_db()
        
        customers_count = db['customers'].count_documents({})
        transactions = db['transactions']
        total_transactions = transactions.count_documents({})
        
        # Get all transactions first
        all_transactions = list(transactions.find({}))
        
        # Group by message_type manually for better control
        message_type_stats = {}
        
        for transaction in all_transactions:
            msg_type = transaction.get('message_type', 'unknown')
            
            if msg_type not in message_type_stats:
                message_type_stats[msg_type] = {
                    'message_type': msg_type,
                    'count': 0,
                    'total_amount': 0,
                    'unique_loans': set(),
                    'unique_folios': set(),
                    'unique_policies': set(),
                    'max_outstanding': 0
                }
            
            stats = message_type_stats[msg_type]
            stats['count'] += 1
            
            # Handle amount
            amount = transaction.get('amount')
            if amount is not None and isinstance(amount, (int, float)):
                stats['total_amount'] += amount
            
            # Handle unique references
            loan_ref = transaction.get('loan_reference')
            if loan_ref:
                stats['unique_loans'].add(loan_ref)
                
            folio_num = transaction.get('folio_number')
            if folio_num:
                stats['unique_folios'].add(folio_num)
                
            policy_num = transaction.get('policy_number')
            if policy_num:
                stats['unique_policies'].add(policy_num)
            
            # Handle outstanding
            outstanding = transaction.get('total_outstanding')
            if outstanding is not None and isinstance(outstanding, (int, float)):
                stats['max_outstanding'] = max(stats['max_outstanding'], outstanding)
        
        # Convert sets to counts
        final_stats = []
        for msg_type, stats in message_type_stats.items():
            final_stats.append({
                'message_type': msg_type,
                'count': stats['count'],
                'total_amount': stats['total_amount'],
                'unique_loans': len(stats['unique_loans']),
                'unique_folios': len(stats['unique_folios']),
                'unique_policies': len(stats['unique_policies']),
                'max_outstanding': stats['max_outstanding']
            })
        
        # Sort by count
        final_stats.sort(key=lambda x: x['count'], reverse=True)
        
        # Recent transactions
        recent_transactions = list(
            transactions.find({}, {
                "message_type": 1, "amount": 1, "created_at": 1,
                "customer_id": 1, "loan_reference": 1, "folio_number": 1,
                "policy_number": 1, "total_outstanding": 1, "_id": 0
            }).sort("created_at", -1).limit(10)
        )
        
        for transaction in recent_transactions:
            if 'created_at' in transaction:
                transaction['created_at'] = transaction['created_at'].isoformat()
        
        return {
            "total_customers": customers_count,
            "total_transactions": total_transactions,
            "message_type_stats": final_stats,
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
                }
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
            }
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
async def get_messages_by_type_demo(message_type: str):
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
                        "from": "$from",  # Include 'from' field
                        "_id": 0
                    }
                }
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
                    "important_points": 1,
                    "from": "$raw_message.from"  # Include 'from' field
                }
            }
        ]
        messages = list(transactions.aggregate(pipeline))
        
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




