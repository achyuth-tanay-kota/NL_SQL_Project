import sqlite3
import pandas as pd

DB_FILE = "data/business_data.db"
CSV_DIR = "data/CSVs"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# ---------------- Helper function ----------------
def get_or_create(cur, table, id_col, values):
    where_clause = " AND ".join([f"{c}=?" for c in values.keys()])
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {where_clause}",
                tuple(values[c] for c in values.keys()))
    row = cur.fetchone()
    if row:
        return row[0]
    placeholders = ", ".join(["?"] * len(values))
    cols = ", ".join(values.keys())
    cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                tuple(values.values()))
    return cur.lastrowid

# ---------------- Loaders per CSV ----------------

def load_balance_sheet():
    df = pd.read_csv(f"{CSV_DIR}/BalanceSheet.csv")
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        cur.execute("""INSERT INTO fact_balance_sheet
                       (financial_period_id, line_item, category, sub_category, sub_sub_category, value)
                       VALUES (?,?,?,?,?,?)""",
                    (pid, r["Line Item"], r["Category"], r["SubCategory"], r["SubSubCategory"], r["Value"]))

def load_cashflow():
    df = pd.read_csv(f"{CSV_DIR}/CashFlowStatement.csv")
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        cur.execute("""INSERT INTO fact_cashflow
                       (financial_period_id, item_description, cashflow_category, value)
                       VALUES (?,?,?,?)""",
                    (pid, r["Item"], r["Category"], r["Value"]))

def load_consolidated_pnl():
    df = pd.read_csv(f"{CSV_DIR}/Consolidated PnL.csv")
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        cur.execute("""INSERT INTO fact_consolidated_pnl
                       (financial_period_id, line_item, value)
                       VALUES (?,?,?)""",
                    (pid, r["Line Item"], r["Value"]))

def load_quarterly_pnl():
    df = pd.read_csv(f"{CSV_DIR}/Quarterly PnL.csv")
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["FinancialYear"]})
        cur.execute("""INSERT INTO fact_quarterly_pnl
                       (financial_period_id, quarter, item_description, category, value)
                       VALUES (?,?,?,?,?)""",
                    (pid, r["Quarter"], r["Item"], r["Category"], r["Value"]))

def load_roce_external():
    df = pd.read_csv(f"{CSV_DIR}/ROCE External.csv")
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        cur.execute("""INSERT INTO fact_roce_external
                       (financial_period_id, particular, value)
                       VALUES (?,?,?)""",
                    (pid, r["Particular"], r["Value"]))

def load_roce_internal():
    df = pd.read_csv(f"{CSV_DIR}/ROCE Internal.csv")
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        port_id = get_or_create(cur, "dim_port", "port_id", {"port_name": r["Port"]})
        cur.execute("""INSERT INTO fact_roce_internal
                       (financial_period_id, business_category, port_id, line_item, value)
                       VALUES (?,?,?,?,?)""",
                    (pid, r["Category"], port_id, r["Line Item"], r["Value"]))

def load_containers():
    df = pd.read_csv(f"{CSV_DIR}/Containers.csv")
    # df.rename(columns={"Entity":"Facility Type","Type":"Business_Type"},inplace = True)
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        port_id = get_or_create(cur, "dim_port", "port_id", {"port_name": r["Port"]})
        if "(" in r["Entity"]:
            facility_name, unit = r["Entity"].split(" (")
            unit = unit.replace(")", "")
        else:
            facility_name, unit = r["Entity"], None
        facility_id = get_or_create(cur, "dim_facility", "facility_id",
                                    {"facility_name": facility_name.strip(), "unit_of_measure": unit})
        cur.execute("""INSERT INTO fact_container_capacity
                       (financial_period_id, port_id, facility_id, business_type, capacity_value_mmt)
                       VALUES (?,?,?,?,?)""",
                    (pid, port_id, facility_id, r.get("Type", "N/A"), r["Value"]))

def load_volumes():
    df = pd.read_csv(f"{CSV_DIR}/Volumes.csv")
    # df.rename(columns={"Port":"Port_Name", "State":"Cargo_Category", "Commodity":"Commodity_Type","Entity":"Customer_Name","Type":"Business_Type", "Value":"Volume_MMT"}, inplace=True)
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        port_id = get_or_create(cur, "dim_port", "port_id", {"port_name": r["Port"]})
        commodity_id = get_or_create(cur, "dim_commodity", "commodity_id",
                                     {"cargo_category": r["State"], "commodity_type": r["Commodity"]})
        customer_id = None
        if pd.notna(r["Entity"]) and r["Entity"] != "N/A":
            customer_id = get_or_create(cur, "dim_customer", "customer_id", {"customer_name": r["Entity"]})
        cur.execute("""INSERT INTO fact_cargo_volumes
                       (financial_period_id, port_id, commodity_id, customer_id, business_type, volume_value_mmt)
                       VALUES (?,?,?,?,?,?)""",
                    (pid, port_id, commodity_id, customer_id, r["Type"], r["Value"]))

def load_roro():
    df = pd.read_csv(f"{CSV_DIR}/RORO.csv")
    for _, r in df.iterrows():
        pid = get_or_create(cur, "dim_period", "period_id", {"financial_year": r["Period"]})
        port_id = get_or_create(cur, "dim_port", "port_id", {"port_name": r["Port"]})
        cur.execute("""INSERT INTO fact_roro
                       (financial_period_id, port_id, allocation_type, ratio_value, number_of_cars)
                       VALUES (?,?,?,?,?)""",
                    (pid, port_id, r["Type"], r["Value"], r["Number of Cars"]))

# ---------------- Run all loaders ----------------
load_balance_sheet()
print('Balance Sheet Done')
load_cashflow()
print('Cashflow Sheet Done')
load_consolidated_pnl()
print('Consolidated Pnl Sheet Done')
load_quarterly_pnl()
print('Quarterly Pnl Sheet Done')
load_roce_external()
print('Roce External Pnl Sheet Done')
load_roce_internal()
print('Roce Internal Pnl Sheet Done')
load_containers()
print('Container Pnl Sheet Done')
load_volumes()
print('Volume Sheet Done')
load_roro()
print('RORO Volume Sheet Done')

conn.commit()
conn.close()

##Adding financial terms to the vector db
from RAG_data_ingestion import create_initial_index
create_initial_index()