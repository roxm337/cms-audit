# 🛡️ CMS Audit Backend

**CMS Audit** is a powerful backend application designed to automate vulnerability scanning for popular Content Management Systems (CMS) like **WordPress** and **Laravel**. It leverages **FastAPI** for its robust API, **Celery** for asynchronous task processing, and **SQLAlchemy** for database interactions. This project provides a reliable and scalable solution for continuously monitoring your CMS installations for known security vulnerabilities.

---

## ✨ Features

- 🔍 **WordPress Scanning**: Integrates with WPScan to identify vulnerabilities in WordPress core, plugins, and themes.
- 🧪 **Laravel Scanning**: Analyzes `composer.lock` files for known vulnerabilities using `composer audit` and the [OSV.dev](https://osv.dev) database.
- ⚙️ **Asynchronous Task Processing**: Uses Celery with Redis to offload scans and keep the API responsive.
- 💾 **Persistent Storage**: Stores scan targets and findings in PostgreSQL or MySQL.
- 🌐 **RESTful API**: Clean endpoints for managing targets and retrieving scan results.
- 🔁 **Real-Time Updates**: Vulnerability findings are updated as background scans complete.

---

## 🏗️ Project Structure

```
cms-audit/
├── app/
│   ├── __init__.py
│   ├── settings.py
│   ├── database.py
│   ├── models.py
│   ├── crud.py
│   ├── celery_app.py
│   ├── tasks.py
│   └── api.py
├── main.py
└── requirements.txt
```

---

## 📋 Prerequisites

- Python 3.8+
- pip
- Redis
- PostgreSQL or MySQL
- WPScan (`gem install wpscan`)
- Composer

---

## 🚀 Installation

```bash
git clone https://github.com/your-username/cms-audit.git
cd cms-audit/backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

## ⚙️ Configuration

Create a `.env` file:

```env
# PostgreSQL
DATABASE_URL="postgresql+psycopg2://postgres:password@localhost/vulntracker"

# MySQL
# DATABASE_URL="mysql+pymysql://user:password@localhost/vulntracker"

REDIS_URL="redis://localhost:6379/0"
SECRET_KEY="your-secret"
WPSCAN_TOKEN="your-wpscan-token"
```

---

## ▶️ Usage

### 1. Initialize the database

```bash
python3 -c "from app.database import Base, engine; Base.metadata.create_all(engine)"
```

### 2. Start FastAPI server

```bash
uvicorn main:app --reload
```

### 3. Start Celery worker

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

---

## 📡 API Examples

**Add Laravel Target:**

```bash
curl -X POST http://127.0.0.1:8000/api/targets/laravel   -F "file=@composer.lock"
```

**Add WordPress Target:**

```bash
curl -X POST http://127.0.0.1:8000/api/targets/wordpress   -H "Content-Type: application/json"   -d '{"url": "http://example.com"}'
```

**List Targets:**

```bash
curl http://127.0.0.1:8000/api/targets
```

**List Findings:**

```bash
curl http://127.0.0.1:8000/api/targets/<target_id>/findings
```

---

## 📄 License

MIT License
