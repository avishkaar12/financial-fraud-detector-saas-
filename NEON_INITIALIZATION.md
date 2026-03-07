# 🎯 NEON DATABASE INITIALIZATION - Step by Step

## YOUR NEXT ACTION: Initialize Your Neon Database

**Time Required**: 5 minutes  
**Difficulty**: Easy ✅  
**Status**: Ready to Execute

---

## STEP 1: Open Neon SQL Editor

1. Go to [neon.tech](https://neon.tech)
2. Sign in to your account
3. Click on your project: **risk-atlas-9d5a6**
4. Click "SQL Editor" on the left sidebar
5. You should see "neondb" database selected

---

## STEP 2: Copy the Schema

You already have the best schema! It's in: `db_schema.sql`

**OR** if you don't have it, use this **exact SQL**:

```sql
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
```

---

## STEP 3: Paste into Neon SQL Editor

1. In the SQL Editor, click the text area
2. **Paste the entire schema** (from above)
3. You should see all the SQL highlighted in the editor

---

## STEP 4: Execute the Schema

1. Click the blue **"Execute"** button (bottom right of SQL Editor)
2. Or press: `Ctrl+Enter`
3. Wait 5-10 seconds for it to complete

---

## STEP 5: Verify Success

If you see this output, **you're done!** ✅

```
COUNT: 0
COUNT: 0
COUNT: 0
```

These are the row counts for your 3 new tables (all should be 0).

---

## ✅ Verification Queries

Run these **one at a time** to confirm everything is working:

### Check 1: Confirm Tables Exist
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
```

**Expected Output**:
```
alerts
model_logs
transactions
```

### Check 2: Confirm Indexes Exist
```sql
SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname;
```

**Expected Output**: 8 indexes listed (idx_alerts_*, idx_model_logs_*, idx_transactions_*)

### Check 3: Test Writing Data
```sql
INSERT INTO transactions 
(transaction_id, amount, transaction_hour, merchant_category, 
 foreign_transaction, location_mismatch, device_trust_score, 
 velocity_last_24h, cardholder_age, is_fraud)
VALUES 
('test-001', 150.50, 14, 'Electronics', 0, 0, 75, 5, 35, false);
```

**Expected**: `INSERT 1` (means 1 row inserted)

### Check 4: Test Reading Data
```sql
SELECT * FROM transactions WHERE transaction_id = 'test-001';
```

**Expected**: Should see your test transaction

### Check 5: Clean Up Test Data
```sql
DELETE FROM transactions WHERE transaction_id = 'test-001';
```

**Expected**: `DELETE 1` (cleaned up successfully)

---

## 🎯 You're Done with Neon! ✅

Your database is now **ready for production**.

Next steps:
1. ✅ **Neon Schema**: COMPLETE (you just did this)
2. ⏭️ **Deploy Backend to Render**: Copy your DATABASE_URL
3. ⏭️ **Deploy Frontend to Vercel**: Firebase config ready
4. ⏭️ **Test End-to-End**: Upload CSV and check database

---

## 📋 Your DATABASE_URL (for Render)

In your Neon dashboard:
1. Go to Connection
2. Copy the connection string
3. It looks like:
   ```
   postgresql://neondb_owner:YOUR_PASSWORD@ep-XXX-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

**Save this!** You'll paste it into Render environment variables.

---

## ❓ Troubleshooting

### "Error: pgcrypto extension not found"
- Type this first: `CREATE EXTENSION IF NOT EXISTS "pgcrypto";`
- Then run the rest of the schema

### "Error: Column references invalid table"
- Check for typos in table names
- Try running schema again (IF NOT EXISTS handles duplicates)

### "Error: Permission denied"
- Click "Database" → "Roles"
- Ensure neondb_owner has all permissions
- Try running with default user

### "No output / query seems stuck"
- Wait 20 seconds (large schema can take time)
- Close and reopen SQL Editor
- Try smaller queries first

### Tables exist but won't insert
- Check constraints: `SELECT * FROM transactions LIMIT 0;`
- Ensure all required fields are provided
- Check data types match schema

---

## 📊 What You Now Have

```
✅ pgcrypto extension (for UUIDs)
✅ transactions table (with 10 fields + indexes)
✅ model_logs table (with 4 fields + indexes)
✅ alerts table (with 5 fields + indexes)
✅ 8 performance indexes
✅ Foreign key relationships
✅ Cascading deletes
✅ Data validation (CHECK constraints)
```

---

## 🚀 Ready for Render

Your backend will connect using:
```
DATABASE_URL=postgresql://neondb_owner:...@ep-nameless-leaf-....-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
```

Everything is **production-ready**! 🎉

---

**Status**: Ready to Deploy  
**Next**: Deploy to Render  
**Time Estimate**: 5 minutes for this step
