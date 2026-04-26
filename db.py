"""Single database access point for the application."""

from contextlib import contextmanager
from typing import Any, Iterator, Optional

import oracledb

from config import Config

# Enable thick mode for older Oracle DB versions (Oracle XE 11.2 detected)
# lib_dir points to the Oracle client shared library folder
try:
    oracledb.init_oracle_client(lib_dir=r"D:\oraclexe\app\oracle\product\11.2.0\server\bin")
except Exception:
    # Already initialized or client not found
    pass

# Ensure CLOBs/BLOBs are returned as strings/bytes instead of LOB locators
oracledb.defaults.fetch_lobs = False

def dict_row_factory(cursor):
    column_names = [col[0].lower() for col in cursor.description]
    def create_row(*args):
        return dict(zip(column_names, args))
    return create_row

# Importable alias for modules that open their own cursors
make_dict_factory = dict_row_factory

def get_connection():
    conn = oracledb.connect(
        user=Config.ORACLE_USER,
        password=Config.ORACLE_PASSWORD,
        dsn=Config.ORACLE_DSN,
    )
    conn.autocommit = False
    return conn

@contextmanager
def connection_scope() -> Iterator[Any]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_query(
    sql: str,
    params: Optional[tuple | list | dict] = None,
    *,
    fetch: str = "none",
    commit: bool = True,
    returning_id: bool = False,
) -> Any:
    """
    fetch: 'none' | 'one' | 'all'
    returning_id: If True, adds an output bind variable for Oracle RETURNING clause.
                  The SQL must include `RETURNING id INTO :out_bind`.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if params is None:
                params = []
            
            out_bind = None
            if returning_id:
                out_bind = cur.var(oracledb.NUMBER)
                if isinstance(params, list):
                    params.append(out_bind)
                elif isinstance(params, tuple):
                    params = list(params)
                    params.append(out_bind)
                elif isinstance(params, dict):
                    params["out_bind"] = out_bind

            cur.execute(sql, params)

            if fetch != "none":
                # Set row factory for queries that return rows
                cur.rowfactory = dict_row_factory(cur)

            result = None
            if fetch == "one":
                result = cur.fetchone()
            elif fetch == "all":
                result = cur.fetchall()
            elif returning_id and out_bind is not None:
                # Get the returned value (it's a list since it could return multiple rows, we want the first)
                vals = out_bind.getvalue()
                if vals:
                    result = int(vals[0])
            
            if commit:
                conn.commit()
            return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_many(sql: str, seq_of_params: list, *, commit: bool = True) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany(sql, seq_of_params)
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
