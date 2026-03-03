from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import requests
from io import StringIO
import joblib
from supabase_client import insert_alert, insert_transaction

app = FastAPI()

# Load the trained model
model = joblib.load("fraud_model.pkl")

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(StringIO(contents.decode("utf-8")))

    # One-hot encode to match training format
    df_encoded = pd.get_dummies(df, columns=["location", "merchant"])

    # Align columns with model input
    X = df_encoded.reindex(columns=model.feature_names_in_, fill_value=0)

    # Predict frauds
    predictions = model.predict(X)
    df["is_fraud"] = predictions

    # Insert all transactions
    for _, row in df.iterrows():
        insert_transaction(row.to_dict())

    # Insert only frauds into alerts
    frauds = df[df["is_fraud"] == 1]
    for _, row in frauds.iterrows():
        insert_alert(row.to_dict())

    return {
        "frauds_detected": len(frauds),
        "alerts": frauds.to_dict(orient="records")
    }

@app.get("/alerts")
def get_alerts():
    url = "https://your-project-id.supabase.co/rest/v1/alerts"
    headers = {
        "apikey": "your-anon-key",
        "Authorization": "Bearer your-anon-key"
    }
    response = requests.get(url, headers=headers)
    return JSONResponse(content=response.json())