"""Initialize Oracle Database for EMS by running all SQL scripts in order."""
import os
import re
import oracledb
from config import Config

# Enable thick mode for Oracle XE 11.2 (thin mode doesn't support 11g)
try:
    oracledb.init_oracle_client(lib_dir=r"D:\oraclexe\app\oracle\product\11.2.0\server\bin")
except Exception as e:
    print(f"Note: init_oracle_client: {e}")


def strip_comments(text):
    """Remove single-line -- comments from a SQL block."""
    lines = [l for l in text.splitlines() if not l.strip().startswith("--")]
    return "\n".join(lines).strip()


def run_script(conn, filepath):
    print(f"\n>>> Running: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on "/" that appears alone on its own line (Oracle block terminator)
    blocks = re.split(r"^\s*/\s*$", content, flags=re.MULTILINE)

    PLSQL_STARTERS = (
        "BEGIN",
        "CREATE OR REPLACE TRIGGER",
        "CREATE OR REPLACE PROCEDURE",
        "CREATE OR REPLACE FUNCTION",
        "CREATE OR REPLACE PACKAGE",
    )

    with conn.cursor() as cur:
        for raw_block in blocks:
            # Strip leading/trailing whitespace
            raw_block = raw_block.strip()
            if not raw_block:
                continue

            # Remove comment lines to get the actual SQL content
            clean_block = strip_comments(raw_block)
            if not clean_block:
                continue  # block was only comments

            is_plsql = any(clean_block.upper().startswith(kw) for kw in PLSQL_STARTERS)

            if is_plsql:
                # Execute PL/SQL block as-is (oracledb needs END; but NOT a trailing ; after END;)
                # The semicolon after END is part of PL/SQL syntax and must stay
                try:
                    cur.execute(clean_block)
                    preview = clean_block[:70].replace("\n", " ")
                    print(f"  OK (PL/SQL): {preview}...")
                except oracledb.DatabaseError as e:
                    preview = clean_block[:90].replace("\n", " ")
                    print(f"  ERROR (PL/SQL): {preview}\n    => {e}")
            else:
                # Split multiple DDL/DML statements separated by semicolons
                stmts = re.split(r";\s*\n|;\s*$", clean_block)
                for stmt in stmts:
                    stmt = stmt.strip()
                    if not stmt or stmt.startswith("--"):
                        continue
                    try:
                        cur.execute(stmt)
                        preview = stmt[:80].replace("\n", " ")
                        print(f"  OK: {preview}")
                    except oracledb.DatabaseError as e:
                        preview = stmt[:90].replace("\n", " ")
                        print(f"  ERROR: {preview}\n    => {e}")

    conn.commit()


def main():
    print(f"Connecting to Oracle: {Config.ORACLE_DSN} as {Config.ORACLE_USER}")
    conn = oracledb.connect(
        user=Config.ORACLE_USER,
        password=Config.ORACLE_PASSWORD,
        dsn=Config.ORACLE_DSN,
    )
    conn.autocommit = False
    print("Connected successfully!\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(base_dir, "database")
    scripts = [
        "01_schema.sql",
        "02_seed.sql",
        "03_sp_views_trigger.sql",
        "04_admin_seed.sql",
    ]

    for script in scripts:
        run_script(conn, os.path.join(db_dir, script))

    conn.close()
    print("\n=== Database initialization complete! ===")


if __name__ == "__main__":
    main()
