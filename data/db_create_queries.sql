-- Dimensions
CREATE TABLE dim_period (
    period_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_year TEXT NOT NULL,
    quarter        TEXT,
    period_type    TEXT
);

CREATE TABLE dim_port (
    port_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    port_name  TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_facility (
    facility_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_name TEXT NOT NULL,
    unit_of_measure TEXT,
    UNIQUE(facility_name, unit_of_measure)
);

CREATE TABLE dim_commodity (
    commodity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    cargo_category TEXT,
    commodity_type TEXT,
    UNIQUE(cargo_category, commodity_type)
);

CREATE TABLE dim_customer (
    customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL UNIQUE
);

-- Facts
CREATE TABLE fact_balance_sheet (
    bs_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    line_item           TEXT,
    category            TEXT,
    sub_category        TEXT,
    sub_sub_category    TEXT,
    value               REAL
);

CREATE TABLE fact_cashflow (
    cf_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    item_description    TEXT,
    cashflow_category   TEXT,
    value               REAL
);

CREATE TABLE fact_consolidated_pnl (
    pnl_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    line_item           TEXT,
    value               REAL
);

CREATE TABLE fact_quarterly_pnl (
    q_pnl_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    quarter             TEXT,
    item_description    TEXT,
    category            TEXT,
    value               REAL
);

CREATE TABLE fact_roce_external (
    roce_ext_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    particular          TEXT,
    value               REAL
);

CREATE TABLE fact_roce_internal (
    roce_int_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    business_category   TEXT,
    port_id             INTEGER REFERENCES dim_port(port_id),
    line_item           TEXT,
    value               REAL
);

CREATE TABLE fact_container_capacity (
    capacity_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    port_id             INTEGER REFERENCES dim_port(port_id),
    facility_id         INTEGER REFERENCES dim_facility(facility_id),
    business_type       TEXT,
    capacity_value_mmt  REAL
);

CREATE TABLE fact_cargo_volumes (
    volume_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    port_id             INTEGER REFERENCES dim_port(port_id),
    commodity_id        INTEGER REFERENCES dim_commodity(commodity_id),
    customer_id         INTEGER REFERENCES dim_customer(customer_id),
    business_type       TEXT,
    volume_value_mmt    REAL
);

CREATE TABLE fact_roro (
    roro_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_period_id INTEGER REFERENCES dim_period(period_id),
    port_id             INTEGER REFERENCES dim_port(port_id),
    allocation_type     TEXT,
    ratio_value         REAL,
    number_of_cars      INTEGER
);
