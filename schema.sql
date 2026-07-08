-- ============================================================
-- Rice Mill Business Intelligence System — Database Schema
-- Engine target: SQLite (dev) / PostgreSQL (prod) — kept ANSI-portable
-- ============================================================

-- 1. SUPPLIERS -------------------------------------------------
CREATE TABLE suppliers (
    supplier_id       INTEGER PRIMARY KEY,
    supplier_name     TEXT NOT NULL,
    region            TEXT,
    contact_phone     TEXT,
    onboarding_date   DATE,
    payment_terms_days INTEGER DEFAULT 15,
    is_active         BOOLEAN DEFAULT 1
);

-- 2. PURCHASES (paddy intake from suppliers) --------------------
CREATE TABLE purchases (
    purchase_id       INTEGER PRIMARY KEY,
    purchase_date     DATE NOT NULL,
    supplier_id       INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    paddy_variety     TEXT NOT NULL,
    quantity_kg       REAL NOT NULL,
    price_per_kg       REAL NOT NULL,
    moisture_pct      REAL,
    rejected_bags     INTEGER DEFAULT 0,
    delivery_delay_days INTEGER DEFAULT 0,
    total_amount      REAL GENERATED ALWAYS AS (quantity_kg * price_per_kg) STORED
);

-- 3. PRODUCTION (milling runs converting paddy -> outputs) -----
CREATE TABLE production (
    production_id     INTEGER PRIMARY KEY,
    production_date    DATE NOT NULL,
    paddy_input_kg     REAL NOT NULL,
    rice_output_kg     REAL NOT NULL,
    bran_output_kg     REAL NOT NULL,
    husk_output_kg     REAL NOT NULL,
    broken_rice_kg     REAL DEFAULT 0,
    recovery_pct       REAL GENERATED ALWAYS AS (rice_output_kg * 100.0 / NULLIF(paddy_input_kg,0)) STORED,
    shift              TEXT,
    machine_id         TEXT
);

-- 4. PRODUCTS (finished-goods catalogue) ------------------------
CREATE TABLE products (
    product_id        INTEGER PRIMARY KEY,
    product_name       TEXT NOT NULL,
    category          TEXT,          -- e.g. Basmati, Sella, Broken, Bran
    unit_cost         REAL,
    unit_price        REAL,
    min_stock_kg       REAL DEFAULT 5000
);

-- 5. INVENTORY (daily stock snapshot by product) -----------------
CREATE TABLE inventory (
    inventory_id       INTEGER PRIMARY KEY,
    snapshot_date       DATE NOT NULL,
    product_id          INTEGER NOT NULL REFERENCES products(product_id),
    quantity_on_hand_kg REAL NOT NULL,
    warehouse           TEXT
);

-- 6. CUSTOMERS ----------------------------------------------------
CREATE TABLE customers (
    customer_id        INTEGER PRIMARY KEY,
    customer_name        TEXT NOT NULL,
    customer_type        TEXT,        -- Wholesaler, Retailer, Exporter
    region               TEXT,
    credit_limit          REAL DEFAULT 0,
    payment_terms_days    INTEGER DEFAULT 30
);

-- 7. SALES ----------------------------------------------------------
CREATE TABLE sales (
    sale_id             INTEGER PRIMARY KEY,
    sale_date            DATE NOT NULL,
    customer_id          INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id           INTEGER NOT NULL REFERENCES products(product_id),
    quantity_kg           REAL NOT NULL,
    selling_price_per_kg  REAL NOT NULL,
    cost_price_per_kg     REAL NOT NULL,
    amount_paid            REAL DEFAULT 0,
    total_amount           REAL GENERATED ALWAYS AS (quantity_kg * selling_price_per_kg) STORED,
    profit                  REAL GENERATED ALWAYS AS (quantity_kg * (selling_price_per_kg - cost_price_per_kg)) STORED,
    outstanding              REAL GENERATED ALWAYS AS (quantity_kg * selling_price_per_kg - amount_paid) STORED
);

-- 8. EMPLOYEES ---------------------------------------------------
CREATE TABLE employees (
    employee_id     INTEGER PRIMARY KEY,
    employee_name    TEXT NOT NULL,
    role             TEXT,
    department        TEXT,
    monthly_salary    REAL,
    hire_date         DATE
);

-- 9. EXPENSES ------------------------------------------------------
CREATE TABLE expenses (
    expense_id    INTEGER PRIMARY KEY,
    expense_date   DATE NOT NULL,
    category       TEXT NOT NULL,     -- Electricity, Diesel, Labour, Packaging, Maintenance, Transport
    amount          REAL NOT NULL,
    notes           TEXT
);

-- 10. MACHINE LOGS ---------------------------------------------------
CREATE TABLE machine_logs (
    log_id          INTEGER PRIMARY KEY,
    log_date         DATE NOT NULL,
    machine_id        TEXT NOT NULL,
    running_hours      REAL,
    downtime_hours     REAL,
    downtime_reason     TEXT,
    maintenance_cost    REAL DEFAULT 0
);

-- 11. ACCOUNTS (chart of accounts) ------------------------------------
CREATE TABLE accounts (
    account_id      INTEGER PRIMARY KEY,
    account_code      TEXT UNIQUE,
    account_name       TEXT NOT NULL,
    account_type        TEXT NOT NULL  -- Asset, Liability, Equity, Revenue, Expense
);

-- 12. JOURNAL ENTRIES (double-entry bookkeeping) -----------------------
CREATE TABLE journal_entries (
    entry_id        INTEGER PRIMARY KEY,
    entry_date        DATE NOT NULL,
    account_id         INTEGER NOT NULL REFERENCES accounts(account_id),
    debit               REAL DEFAULT 0,
    credit              REAL DEFAULT 0,
    description          TEXT,
    reference_type        TEXT,   -- Purchase, Sale, Expense, Manual
    reference_id           INTEGER
);

-- 13. FORECASTS (model outputs, stored for the SQL Explorer / dashboards) --
CREATE TABLE forecasts (
    forecast_id      INTEGER PRIMARY KEY,
    forecast_date      DATE NOT NULL,
    metric               TEXT NOT NULL,   -- production_kg, sales_kg, revenue, cash_flow
    predicted_value        REAL,
    lower_bound              REAL,
    upper_bound              REAL,
    model_used                TEXT
);

-- Helpful indexes -------------------------------------------------------
CREATE INDEX idx_purchases_date ON purchases(purchase_date);
CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_production_date ON production(production_date);
CREATE INDEX idx_inventory_date ON inventory(snapshot_date);
CREATE INDEX idx_journal_date ON journal_entries(entry_date);
