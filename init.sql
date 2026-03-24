-- ============================================================
-- Waterborne Disease Monitoring System — Database Initialization
-- This file is automatically run by MySQL on first container start.
-- ============================================================

CREATE DATABASE IF NOT EXISTS waterborne_db;
USE waterborne_db;

-- ── Villages ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS villages (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Seed North East India regions
INSERT IGNORE INTO villages (id, name) VALUES
    (1, 'Assam'),
    (2, 'Arunachal Pradesh'),
    (3, 'Manipur'),
    (4, 'Meghalaya'),
    (5, 'Mizoram'),
    (6, 'Nagaland'),
    (7, 'Sikkim'),
    (8, 'Tripura'),
    (9, 'Bodoland Territorial Region'),
    (10, 'Karbi Anglong');

-- ── Users ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(100),
    username     VARCHAR(100) NOT NULL UNIQUE,
    password     VARCHAR(255) NOT NULL,
    role         ENUM('admin','asha_worker','volunteer','patient') NOT NULL,
    phone_number VARCHAR(20),
    village_id   INT,
    status       VARCHAR(20) DEFAULT 'active',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (village_id) REFERENCES villages(id)
);

-- ── Health Reports ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_reports (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT,
    village_id   INT,
    symptoms     TEXT,
    disease_type VARCHAR(100),
    patient_name VARCHAR(100),
    patient_age  INT,
    patient_phone VARCHAR(20),
    report_date  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES users(id),
    FOREIGN KEY (village_id) REFERENCES villages(id)
);

-- ── Water Reports ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS water_reports (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    village_id         INT,
    ph_level           DECIMAL(4,2),
    turbidity          DECIMAL(6,2),
    contamination_type VARCHAR(100),
    report_date        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (village_id) REFERENCES villages(id)
);

-- ── Alerts ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    village_id INT,
    risk_level ENUM('LOW','MEDIUM','HIGH') NOT NULL,
    message    TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (village_id) REFERENCES villages(id)
);

-- ── AI Water Analysis History ────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_water_analysis (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    village_id         INT,
    image_path         VARCHAR(255),
    drinkable          BOOLEAN,
    contamination_prob DECIMAL(4,3),
    confidence         DECIMAL(4,3),
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (village_id) REFERENCES villages(id)
);
