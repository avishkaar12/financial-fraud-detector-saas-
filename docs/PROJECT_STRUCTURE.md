# Project Structure

## Root
- `backend/` - FastAPI app, ML model integration, utilities, tests
- `website/` - Single production frontend (React via browser ESM)
- `sample_transactions.csv` - Valid CSV template for `/detect`
- `.env.example` - Required environment variables template

## backend/
- `main.py` - API entrypoint and route handlers
- `db.py` - PostgreSQL data access layer
- `auth.py` - Firebase ID token verification
- `requirements.txt` - Python dependencies
- `fraud_model.pkl` - Trained fraud detection model
- `model_columns.json` - Strict model input feature order

### backend/utils/
- `schema.py` - Input schema and required fields
- `preprocessing.py` - Data validation + model feature alignment
- `explain.py` - SHAP explanations + fraud reason/severity logic

### backend/training/
- `train_model.py` - Offline retraining script
- `creditcard.csv` - Training dataset

### backend/tests/
- `test_preprocessing.py` - Feature alignment validation tests
- `test_api.py` - `/detect` schema and success path tests

## Recommended Presentation Flow
1. Explain architecture and input schema.
2. Show `/health` and sample CSV.
3. Run `/detect` and display fraud result + explanation.
4. Show `/alerts` and `/analytics` outputs.
5. Mention testing + deployment path.
