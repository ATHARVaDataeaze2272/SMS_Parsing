import logging

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