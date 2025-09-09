VDB_COLLECTION_NAME="terminology"
VDB_PERSIST_DIR="./data/chroma_db"
VDB_TOP_K_VALUE=10
CHAT_OPENAI_MODEL_NAME="gpt-4o"
DB_SCHEMA_PATH= 'data/database_schema.txt'
DB_PATH="data/business_data.db"

SQL_ROW_LIMIT = 50

forbidden_sql_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'attach', 'pragma', 'create']
debug_mode = False
checkpoint_db_path = "checkpoints.sqlite"

API_HOST='localhost'
API_PORT=8080