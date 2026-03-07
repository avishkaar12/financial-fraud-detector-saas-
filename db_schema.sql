-- Risk Atlas - PostgreSQL Schema for Neon
-- This is the production schema optimized for PostgreSQL/Neon
-- Run this in Neon SQL Editor to initialize the database

-- Enable UUID support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Transactions table: stores all processed transactions
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id TEXT PRIMARY KEY,
  amount NUMERIC NOT NULL CHECK (amount >= 0),
  transaction_hour INTEGER NOT NULL CHECK (transaction_hour BETWEEN 0 AND 23),
  merchant_category TEXT NOT NULL,
  foreign_transaction INTEGER NOT NULL CHECK (foreign_transaction IN (0, 1)),
  location_mismatch INTEGER NOT NULL CHECK (location_mismatch IN (0, 1)),
  device_trust_score INTEGER NOT NULL CHECK (device_trust_score BETWEEN 0 AND 100),
  velocity_last_24h INTEGER NOT NULL CHECK (velocity_last_24h >= 0),
  cardholder_age INTEGER NOT NULL CHECK (cardholder_age > 0),
  is_fraud BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model logs: stores prediction details for audit trail
CREATE TABLE IF NOT EXISTS model_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id TEXT REFERENCES transactions(transaction_id) ON DELETE CASCADE,
  predicted_fraud BOOLEAN NOT NULL,
  probability NUMERIC NOT NULL CHECK (probability >= 0 AND probability <= 1),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts table: stores high-risk transactions flagged for investigation
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id TEXT REFERENCES transactions(transaction_id) ON DELETE CASCADE,
  reason TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
  status TEXT DEFAULT 'open',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_transactions_is_fraud ON transactions(is_fraud);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON transactions(merchant_category);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_logs_created_at ON model_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_logs_transaction_id ON model_logs(transaction_id);

-- Verify tables created successfully
SELECT COUNT(*) AS total_transactions FROM transactions;
SELECT COUNT(*) AS total_model_logs FROM model_logs;
SELECT COUNT(*) AS total_alerts FROM alerts;

