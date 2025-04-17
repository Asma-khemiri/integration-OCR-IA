import os
from dotenv import load_dotenv

load_dotenv()

ABBYY_APP_ID = os.getenv("ABBYY_APP_ID")
ABBYY_PASSWORD = os.getenv("ABBYY_PASSWORD")
OCR_API_URL = os.getenv("ABBYY_OCR_URL")
TASK_STATUS_URL = os.getenv("ABBYY_STATUS_URL")
