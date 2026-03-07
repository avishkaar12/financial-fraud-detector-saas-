# 🗄️ NEON DATABASE SETUP - Quick Reference

## ✅ What's Ready

Your Neon database schema is **production-optimized** with:
- ✅ UUID primary keys (better than SERIAL)
- ✅ TIMESTAMPTZ for timezone-aware timestamps
- ✅ NUMERIC types for money/probability precision
- ✅ pgcrypto extension for UUID generation
- ✅ Cascading deletes (data integrity)
- ✅ Smart check constraints (data validation)
- ✅ Performance indexes

## 📋 Tables Explained

### **transactions** table
```sql
transaction_id (TEXT)       -- Primary key, never changes
amount (NUMERIC)            -- Transaction amount (allows decimals)
transaction_hour (INT)      -- 0-23 hour of day
merchant_category (TEXT)    -- Store type
foreign_transaction (INT)   -- 0=domestic, 1=foreign
location_mismatch (INT)     -- 0=match, 1=mismatch
device_trust_score (INT)    -- 0-100 risk score
velocity_last_24h (INT)     -- Number of txns in 24h
cardholder_age (INT)        -- Customer age
is_fraud (BOOLEAN)          -- Prediction: true/false
created_at (TIMESTAMPTZ)    -- Auto timestamp
```

### **model_logs** table
```sql
id (UUID)                   -- Auto-generated unique ID
transaction_id (TEXT)       -- Foreign key to transactions
predicted_fraud (BOOLEAN)   -- Model prediction
probability (NUMERIC)       -- 0.0 to 1.0 confidence
created_at (TIMESTAMPTZ)    -- Auto timestamp
```

### **alerts** table
```sql
id (UUID)                   -- Auto-generated unique ID
transaction_id (TEXT)       -- Foreign key to transactions
reason (TEXT)               -- Why fraud was flagged
severity (TEXT)             -- 'low', 'medium', 'high'
status (TEXT)               -- 'open', 'closed', etc
created_at (TIMESTAMPTZ)    -- Auto timestamp
```

## 🗂️ Indexes (Fast Queries)

```sql
✅ idx_transactions_is_fraud       -- Find fraud transactions fast
✅ idx_transactions_created_at     -- Recent transactions first
✅ idx_transactions_merchant       -- Group by merchant_category
✅ idx_alerts_status               -- Filter by status
✅ idx_alerts_severity             -- Group by severity
✅ idx_alerts_created_at           -- Recent alerts first
✅ idx_model_logs_created_at       -- Audit trail queries
✅ idx_model_logs_transaction_id    -- Look up model logs
```

## 📊 Sample Queries

### Get fraud rate by day
```sql
SELECT 
  DATE(created_at) as day,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) as fraud_count,
  ROUND(100.0 * SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) / COUNT(*), 2) as fraud_rate
FROM transactions
GROUP BY DATE(created_at)
ORDER BY day DESC;
```

### Get high-severity alerts
```sql
SELECT 
  a.id,
  a.transaction_id,
  a.reason,
  a.severity,
  a.status,
  t.amount,
  t.merchant_category,
  a.created_at
FROM alerts a
JOIN transactions t ON a.transaction_id = t.transaction_id
WHERE a.severity = 'high'
ORDER BY a.created_at DESC
LIMIT 50;
```

### Check model accuracy
```sql
SELECT 
  ml.predicted_fraud,
  t.is_fraud,
  COUNT(*) as count
FROM model_logs ml
JOIN transactions t ON ml.transaction_id = t.transaction_id
GROUP BY ml.predicted_fraud, t.is_fraud;
```

### Latest 10 transactions
```sql
SELECT 
  transaction_id,
  amount,
  merchant_category,
  is_fraud,
  created_at
FROM transactions
ORDER BY created_at DESC
LIMIT 10;
```

## 🔧 Maintenance

### Check table sizes
```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check database growth
```sql
SELECT 
  pg_size_pretty(pg_database_size(current_database())) as db_size;
```

### Vacuum and analyze (for performance)
```sql
VACUUM ANALYZE transactions;
VACUUM ANALYZE model_logs;
VACUUM ANALYZE alerts;
```

## 🚀 Connection String

```
postgresql://neondb_owner:npg_Pj8lpBs0YLib@ep-nameless-leaf-aic9mhib-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
```

**Backend uses**: `DATABASE_URL` environment variable  
**Connection pooling**: Enabled via `-pooler` in host  
**SSL Mode**: `require` (mandatory)

## ✅ Verification Queries

Run these in Neon SQL Editor to verify setup:

```sql
-- Check extensions
SELECT * FROM pg_extension WHERE extname = 'pgcrypto';

-- Check tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check indexes exist
SELECT indexname FROM pg_indexes WHERE schemaname = 'public';

-- Check table row counts
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM model_logs;
SELECT COUNT(*) FROM alerts;

-- Test write (insert dummy transaction)
INSERT INTO transactions 
(transaction_id, amount, transaction_hour, merchant_category, 
 foreign_transaction, location_mismatch, device_trust_score, 
 velocity_last_24h, cardholder_age, is_fraud)
VALUES 
('test-txn-1', 99.99, 14, 'Test', 0, 0, 75, 5, 30, FALSE);

-- Read back
SELECT * FROM transactions WHERE transaction_id = 'test-txn-1';

-- Clean up test
DELETE FROM transactions WHERE transaction_id = 'test-txn-1';
```

## 📞 Troubleshooting

### "Connection refused"
- Check CONNECTION_URL is correct in Neon console
- Verify IP whitelist (should be automatic)
- Test in Neon SQL Editor first

### "SSL error"
- Ensure `sslmode=require` in connection string
- Neon requires SSL - it's not optional

### "Permission denied"
- Use neondb_owner credentials
- Don't use service_role (it's for Supabase)

### "Disk quota exceeded"
- Check table sizes with query above
- Archive old alerts/transactions
- Upgrade Neon plan if needed

### "Connection pool exhausted"
- Reducer of concurrent connections in app
- Use Neon's built-in connection pooling (-pooler)
- Check for connection leaks in backend

## 📈 Performance Tips

1. **Add indexes for queries you run frequently**
   ```sql
   CREATE INDEX idx_high_probability ON model_logs(probability DESC) 
   WHERE predicted_fraud = TRUE;
   ```

2. **Archive old data monthly**
   ```sql
   -- Move old alerts to archive
   CREATE TABLE alerts_archive AS 
   SELECT * FROM alerts WHERE created_at < NOW() - INTERVAL '90 days';
   DELETE FROM alerts WHERE created_at < NOW() - INTERVAL '90 days';
   ```

3. **Monitor with these reports**
   - Daily row counts
   - Growth trends
   - Query performance

## 🎯 What's Next

1. ✅ Schema initialized (you're here)
2. ⏭️ Deploy backend to Render (connects to this DB)
3. ⏭️ Deploy frontend to Vercel (calls backend API)
4. ⏭️ Upload sample CSV to test flow
5. ⏭️ Monitor database growth

---

**Status**: ✅ **Ready to Deploy**  
**Schema Version**: 1.0 (Production)  
**Last Updated**: March 7, 2026
