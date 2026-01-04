from kafka import KafkaConsumer
import json, joblib
import pandas as pd

model = joblib.load("/home/julius-irungu/Desktop/Projects/fraud-pipeline/model/fraud.pkl")

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers=["localhost:9093"],
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

for msg in consumer:
    # Create a small DataFrame so the feature names match
    x = pd.DataFrame([[msg.value["amount"]]], columns=["amount"])
    pred = model.predict(x)[0]
    
    if pred == 1:
        print(f"🚨 FRAUD DETECTED: {msg.value}")
    else:
        # Optional: print a dot to show it's working
        print(".", end="", flush=True)