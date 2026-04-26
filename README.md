# EMS — Smart Recruitment (Oracle Database + AI unified)

Single Flask + Oracle Database application with one runtime flag that switches ranking between **Database Systems mode** (stored procedure + SQL views) and **AI mode** (PDF text, spaCy phrase matching into `CandidateSkills`, scikit-learn TF-IDF cosine similarity, optional semantic similarity). The HTTP API and web UI are identical in both modes.

## Prerequisites

- Python 3.10+
- Oracle Database (XE 11.2+ or 23c Free)
- Oracle Client Libraries (Required for thick mode, detected at `D:\oraclexe\app\oracle\product\11.2.0\server\bin`)

## Database setup

The application uses an automated initialization script for Oracle Database.

1.  Ensure your Oracle Database instance is running.
2.  Run the initialization script to create sequences, tables, triggers, and procedures:

```bash
python init_db.py
```

This runs the scripts in `database/` in order:
- `01_schema.sql` — tables, sequences, and auto-increment triggers
- `02_seed.sql` — `EducationLevels` and `Skills` lookup data
- `03_sp_views_trigger.sql` — `sp_CalculateCandidateScore` (PL/SQL), views, and audit trigger
- `04_admin_seed.sql` — default admin user (development)

Default admin login: `admin@ems.local` / `admin123`.

## Python environment

```bash
cd d:\EMS
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Configuration (environment variables)

| Variable | Purpose |
|----------|---------|
| `ORACLE_USER` | Default `ems_user` |
| `ORACLE_PASSWORD` | Default `abc123` |
| `ORACLE_DSN` | Default `localhost:1521/xe` |
| `SECRET_KEY` | Flask session secret (set in production) |
| `USE_AI_RANKING` | `true` / `false` — **`false`** = DBS stored procedure ranking; **`true`** = AI TF-IDF |
| `USE_SEMANTIC_RANKING` | `true` only if sentence-transformers is installed |

## Run the application

```bash
set ORACLE_PASSWORD=yourpassword
set USE_AI_RANKING=false
python run.py
```

Open `http://127.0.0.1:5000/`.

- **DBS demo**: `USE_AI_RANKING=false` — scores calculated via Oracle PL/SQL `sp_CalculateCandidateScore`.
- **AI demo**: `USE_AI_RANKING=true` — scores calculated via scikit-learn TF-IDF in `app/ranking_ai.py`.

## Project layout

| Path | Role |
|------|------|
| [`config.py`](config.py) | Oracle settings, flags |
| [`db.py`](db.py) | `oracledb` connection with dictionary factory and thick mode init |
| [`init_db.py`](init_db.py) | Oracle-specific SQL script runner |
| [`app/blueprints/`](app/blueprints/) | `auth`, `jobs`, `applications`, `ranking`, `admin` |
| [`database/`](database/) | Oracle-compatible SQL scripts |

## API Overview

- `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/jobs`, `POST /api/jobs`, `GET /api/jobs/skills`
- `POST /api/applications` (PDF resume upload)
- `GET /api/ranking/<job_id>`
- `GET /api/admin/users`, `/api/admin/audit`
