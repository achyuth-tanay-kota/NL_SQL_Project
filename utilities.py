import sqlite3
import json
import re
from langchain_community.utilities import SQLDatabase
import config


def update_schema_file(db_relative_path, schema_file_path):
    db = SQLDatabase.from_uri(f"sqlite:///{db_relative_path}")
    with open(schema_file_path, 'w') as f:
        f.write(db.get_table_info())


def is_safe_sql(sql: str) -> bool:
    """Check if the sql statement is safe to execute."""
    forbidden = config.forbidden_sql_keywords
    s = sql.lower()
    if any(k in s for k in forbidden):
        return False

    # if not re.search(r'^\s*select\b', s, flags=re.IGNORECASE):
    #     return False

    return True

#unused
def format_rows_from_cursor(cur, max_rows: int):
    cols = [c[0] for c in cur.description] if cur.description else []
    rows = []
    for i, r in enumerate(cur.fetchall()):
        if i >= max_rows:
            break
        rows.append(dict(zip(cols, r)))
    return rows


def execute_sql(sql):
    conn = sqlite3.connect(config.DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        conn.close()
        return cols, rows, ''
    except Exception as e:
        print('Exception occured during executing the sql:', str(e))
        conn.close()
        return [], [], str(e)


if __name__ == "__main__":
    update_schema_file('data/business_data.db', './data/database_schema.txt')
    # print(is_safe_sql('select * from dim_port (alter table dim port)'))
