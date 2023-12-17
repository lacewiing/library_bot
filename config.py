# config.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
username = os.getenv('user')
password = os.getenv('password')
host = os.getenv('host')
database_name = os.getenv('database_name')

# Define the cursor as a global variable
global cursor

# Database initialization
def init_db():
    global cursor
    # Establish connection and cursor
    conn = psycopg2.connect(user=username, password=password, host=host, database=database_name)
    cursor = conn.cursor()
    return [conn, cursor]

    # Additional database setup code if needed
