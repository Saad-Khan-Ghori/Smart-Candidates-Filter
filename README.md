# EMS Recruitment — Intelligent Talent Matching Platform

EMS (Enterprise Management System) Recruitment is a high-performance, automated talent acquisition platform built with Flask and Oracle Database. It leverages intelligent filtering and profile alignment analysis to surface the best candidates for your organization.

## Key Features

*   **Intelligent Talent Matching**: Proprietary matching engine that analyzes candidate competencies and alignment with role requirements.
*   **Automated Profile Screening**: Seamless PDF resume processing with automatic identification of professional skills.
*   **Premium Glassmorphism UI**: State-of-the-art dark mode interface designed for optimal recruiter and candidate experience.
*   **Enterprise-Grade Backend**: Powered by Oracle Database with robust PL/SQL stored procedures and views for high-speed data processing.
*   **Full Admin Suite**: Comprehensive oversight for user management, job monitoring, and secure audit logging.

## Tech Stack

*   **Frontend**: HTML5, Vanilla CSS (Premium Glassmorphism), JavaScript (Fetch API)
*   **Backend**: Flask (Python)
*   **Database**: Oracle Database (XE 11.2+, 23c Free)
*   **Connectivity**: `oracledb` (Thick Mode enabled for legacy support)
*   **Processing**: NLP-based skill identification and profile scoring

## Prerequisites

- Python 3.10+
- Oracle Database instance
- Oracle Client Libraries (detected automatically in Thick Mode)

## Getting Started

### 1. Initialize the Environment

```bash
# Clone the repository (if applicable)
# git clone <your-repo-url>
# cd EMS

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Database Configuration

Ensure your Oracle credentials are set in `config.py` or via environment variables:

- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_DSN`

Run the automated initialization script to set up the schema:

```bash
python init_db.py
```

### 3. Run the Application

```bash
python run.py
```

Open your browser at `http://localhost:5000`.

## Administrative Access

Default development credentials:
- **Email**: `admin@ems.local`
- **Password**: `admin123`

## Configuration Options

Toggle between standard and enhanced matching in `config.py`:
- `USE_AI_RANKING`: Enables/Disables intelligent matching engine.
- `USE_SEMANTIC_RANKING`: Enables deep semantic similarity analysis (requires `sentence-transformers`).

---

*Developed with focus on performance, security, and user experience.*
