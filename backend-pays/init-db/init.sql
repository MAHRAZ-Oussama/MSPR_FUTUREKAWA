CREATE TABLE IF NOT EXISTS warehouses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    country VARCHAR(2) NOT NULL,
    manager_email VARCHAR(150),
    target_temp_c DECIMAL(4,1),
    target_humidity DECIMAL(4,1),
    tolerance_temp DECIMAL(3,1),
    tolerance_hum DECIMAL(3,1)
);

CREATE TABLE IF NOT EXISTS lots (
    id VARCHAR(50) PRIMARY KEY,
    warehouse_id INT REFERENCES warehouses(id),
    storage_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'CONFORME',
    variete VARCHAR(50),
    poids_kg DECIMAL(8,2)
);

CREATE INDEX IF NOT EXISTS idx_lots_storage_date ON lots(storage_date ASC);

CREATE TABLE IF NOT EXISTS measurements (
    id BIGSERIAL PRIMARY KEY,
    warehouse_id INT REFERENCES warehouses(id),
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    temperature_c DECIMAL(4,1),
    humidity_pct DECIMAL(4,1)
);

CREATE INDEX IF NOT EXISTS idx_measurements_wh_time ON measurements(warehouse_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    warehouse_id INT REFERENCES warehouses(id),
    lot_id VARCHAR(50) REFERENCES lots(id),
    alert_type VARCHAR(30) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    email_sent BOOLEAN DEFAULT FALSE
);
