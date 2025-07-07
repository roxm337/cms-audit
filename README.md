CMS Audit Backend
📝 Overview
cms-audit is a powerful backend application designed to automate vulnerability scanning for popular Content Management Systems (CMS) like WordPress and Laravel. It leverages FastAPI for its robust API, Celery for asynchronous task processing, and SQLAlchemy for database interactions. This project aims to provide a reliable and scalable solution for continuously monitoring your CMS installations for known security vulnerabilities.

✨ Features
WordPress Scanning: Integrates with WPScan to identify vulnerabilities in WordPress core, plugins, and themes.

Laravel Scanning: Analyzes composer.lock files for known vulnerabilities using Composer Audit and OSV (Open Source Vulnerabilities) database.

Asynchronous Task Processing: Uses Celery to offload time-consuming scans to background workers, ensuring a responsive API.

Persistent Storage: Stores scan targets and findings in a PostgreSQL (or MySQL) database.

RESTful API: Provides a clean and intuitive API for managing targets and retrieving scan results.

Real-time Updates: Findings are updated in the database as scans complete.

🏗️ Project Structure
'''
cms-audit/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── settings.py           # Configuration settings (DB, Redis, API tokens)
│   │   ├── database.py           # SQLAlchemy engine, session, and DB dependency
│   │   ├── models.py             # SQLAlchemy ORM models for Target and Finding
│   │   ├── crud.py               # Database Create, Read, Update, Delete operations
│   │   ├── celery_app.py         # Celery application instance
│   │   └── tasks.py              # Celery tasks for WordPress and Laravel scanning
│   ├── main.py                   # FastAPI application entry point
│   └── requirements.txt          # Python dependencies
└── README.md                     # This file
'''
📋 Prerequisites
Before running this project, ensure you have the following installed on your system:

Python 3.8+

pip (Python package installer)

PostgreSQL (or MySQL, see "Database Configuration" below)

Ensure the database server is running.

You'll need a database named vulntracker and a user with access.

Redis

Ensure the Redis server is running.

WPScan CLI Tool

WPScan is a Ruby Gem. Follow its official installation guide (e.g., gem install wpscan).

Obtain a WPScan API Token from wpscan.com (a free token is sufficient for basic use).

Composer (PHP dependency manager)

Used for Laravel composer.lock file analysis. Follow its official installation guide.

🚀 Installation
Follow these steps to get the project up and running:

Clone the repository:

git clone https://github.com/your-username/cms-audit.git # Replace with your repo URL
cd cms-audit/backend

Create and activate a Python virtual environment:

python3 -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate.bat

Install Python dependencies:
Make sure your requirements.txt file has compatible pydantic versions. It should look like this (or with a newer compatible pydantic 2.x version):

fastapi==0.111.0
uvicorn[standard]==0.30.0
SQLAlchemy==2.0.30
psycopg[binary]==3.1.19
pydantic==2.7.1 # Ensure this is compatible with pydantic-settings and fastapi
pydantic-settings==2.2.1
celery==5.3.6
redis==5.0.3
httpx==0.27.0
python-multipart==0.0.9

Then install:

pip install -r requirements.txt

⚙️ Configuration
Create a .env file in the backend/ directory (the same directory as main.py) and populate it with your database credentials, Redis URL, and WPScan API token:

DATABASE_URL="postgresql+psycopg2://postgres:your_postgres_password@localhost/vulntracker"
REDIS_URL="redis://localhost:6379/0"
SECRET_KEY="a_very_long_and_random_secret_key_for_jwt_security_at_least_32_chars_long"
WPSCAN_TOKEN="YOUR_WPSCAN_API_TOKEN_FROM_WPSCAN.COM"

Replace the placeholder values:

your_postgres_password: The password for your PostgreSQL postgres user.

a_very_long_and_random_secret_key_for_jwt_security_at_least_32_chars_long: A strong, randomly generated secret key (e.g., using openssl rand -hex 32).

YOUR_WPSCAN_API_TOKEN_FROM_WPSCAN.COM: The API token you obtained from wpscan.com.

Database Configuration (MySQL Alternative)

If you prefer to use MySQL instead of PostgreSQL:

Modify requirements.txt:

Remove psycopg[binary].

Add a MySQL driver, e.g., pymysql.

# ...
-psycopg[binary]==3.1.19
+pymysql
# ...

Then run pip install -r requirements.txt.

Update .env:
Change the DATABASE_URL to a MySQL connection string (e.g., using pymysql):

DATABASE_URL="mysql+pymysql://user:password@localhost:3306/vulntracker"

(Replace user, password, localhost:3306, and vulntracker with your MySQL details).

Ensure MySQL server is running and you have created the vulntracker database.

▶️ Usage
You will need at least two separate terminal windows to run the FastAPI application and the Celery worker.

1. Initialize the Database Schema

This command creates all necessary tables in your configured database. Run this once after setting up your database and .env file.

python3 -c "from app.database import Base, engine; Base.metadata.create_all(engine)"

2. Start the FastAPI Application

In your first terminal window:

cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

The API will be accessible at http://127.0.0.1:8000. You can view the interactive API documentation (Swagger UI) at http://127.0.0.1:8000/docs.

3. Start the Celery Worker

In a second terminal window (activate your virtual environment here too):

cd backend
source venv/bin/activate
celery -A app.celery_app.celery_app worker --loglevel=info

This worker will process the vulnerability scanning tasks asynchronously.

4. (Optional) Start Celery Beat Scheduler

If you implement periodic tasks (e.g., scheduled scans), run Celery Beat in a third terminal window:

cd backend
source venv/bin/activate
celery -A app.celery_app.celery_app beat --loglevel=info

Interacting with the API

You can use the Swagger UI (http://127.0.0.1:8000/docs) or curl to interact with the API.

Add a Laravel Target (with a composer.lock file):

# Create a dummy composer.lock for testing (or use a real one)
# echo '{"packages": [{"name": "monolog/monolog", "version": "2.9.0"}]}' > dummy_composer.lock

curl -X 'POST' \
  'http://127.0.0.1:8000/api/targets/laravel' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@./dummy_composer.lock;type=application/json'

Add a WordPress Target:

curl -X 'POST' \
  'http://127.0.0.1:8000/api/targets/wordpress' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "url": "http://test.wordpress.com"
}'

(Replace http://test.wordpress.com with a real WordPress URL you have permission to scan).

List All Targets:

curl -X 'GET' \
  'http://127.0.0.1:8000/api/targets' \
  -H 'accept: application/json'

List Findings for a Specific Target:
(Replace YOUR_TARGET_ID with the id obtained from adding a target)

curl -X 'GET' \
  'http://127.0.0.1:8000/api/targets/YOUR_TARGET_ID/findings' \
  -H 'accept: application/json'

🤝 Contributing
Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

📄 License
This project is open-source and available under the MIT License.

