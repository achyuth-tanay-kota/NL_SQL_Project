import sqlite3

DB_FILE = "data/business_data.db"
DB_CREATE_SCHEMA_FILE = "data/db_create_queries.sql"

def create_empty_tables():
    initialization_queries = open(DB_CREATE_SCHEMA_FILE).read().split(';')

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for query in initialization_queries:
        cur.execute(query+';')

    conn.commit()
    conn.close()

def test_table_creation(table_name):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    results = cur.execute('SELECT * FROM {} LIMIT 5'.format(table_name))

    print([item[0] for item in cur.description])
    for row in results:
        print(row)

    conn.close()


if __name__ == '__main__':
    # create_empty_tables()
    test_table_creation('dim_customer')