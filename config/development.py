import os
import logging

LOG_LEVEL = logging.DEBUG
PRESERVE_CONTEXT_ON_EXCEPTION = True
DEBUG = False
SESSION_COOKIE_SAMESITE = 'strict'
SESSION_COOKIE_PATH = '/'


ROOT_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..'))
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
UPLOAD_FOLDER = os.path.join(ROOT_DIR, "uploads")
EXTRACTED_FOLDER = os.path.join(ROOT_DIR, "save_extracted")
UNZIP_FOLDER = os.path.join(ROOT_DIR, "unzip_folder")
TEMP_FOLDER = os.path.join(ROOT_DIR, "temp_folder")
IMGS_TEMP = os.path.join(ROOT_DIR, "temp_image")
RULE_JSON = os.path.join(ROOT_DIR, "rule_json")
INT_JSON = os.path.join(ROOT_DIR, "int_json")
RESULT_JSON = os.path.join(ROOT_DIR, "result_data")

STATIC_DIR = os.path.join(ROOT_DIR, "medical", "uploads")

DATA_OUTPUT = os.path.join(ROOT_DIR, "medical", "data_output")
EXTRA_DATA =  os.path.join(DATA_OUTPUT,"extra_data")


SECRET_KEY = "Kc5c3zTk'-3<&BdL:P92O{_(:-NkY+"

DB_USERNAME = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = ""
DB_CONNECTION_STRING = 'mysql+mysqlconnector://' + DB_USERNAME + ':' + DB_PASSWORD + '@' + DB_HOST + ':' + DB_PORT + '/' + DB_NAME

EMAIL = ""
PASS = ""

ENCRYPTED_KEY = ""

UI_ENC_SALT = ""
UI_ENC_KEY = ""


VENDOR_DATASET = ''



