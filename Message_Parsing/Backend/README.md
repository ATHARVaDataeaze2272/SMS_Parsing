Financial SMS Analyzer
A FastAPI-based application for analyzing financial SMS messages, classifying them, extracting data, and storing results in MongoDB.
Setup

Clone the repository:
git clone <repository-url>
cd financial_sms_analyzer


Create a .env file in the project root with the following:
MONGODB_URL=<your-mongodb-url>
GOOGLE_API_KEY=<your-google-api-key>


Install dependencies:
pip install -r requirements.txt


Run the application:
python main.py



Docker Deployment

Build the Docker image:
docker build -t financial-sms-analyzer .


Run the Docker container:
docker run --env-file .env -p 8000:8000 financial-sms-analyzer



API Endpoints

GET /: Health check
GET /health: Detailed health check
POST /analyze-message: Analyze a single SMS message
POST /upload-csv: Upload and process a CSV file
GET /processing-status: Get CSV processing status
GET /customers: List customers
GET /customers/{customer_id}/transactions: Get customer transactions
GET /customers/{customer_id}/summary: Get customer transaction summary
GET /customers/{customer_id}/messages: Get customer raw messages
GET /analytics/summary: Get analytics summary
GET /message-type-counts: Get message type counts
GET /messages: Get messages by type

Dependencies
See requirements.txt for a list of Python dependencies.
Logging
Logs are written to financial_sms.log and the console with DEBUG level.
