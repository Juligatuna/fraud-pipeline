from kafka import KafkaConsumer
import json, pandas as pd
import os

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers=["localhost:9093"],
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

buffer = []

for msg in consumer:
    buffer.append(msg.value)
    print(f"Received: {msg.value}")
    if len(buffer) >= 10:
        df = pd.DataFrame(buffer)
        path = "/home/julius-irungu/Desktop/Projects/fraud-pipeline/data/raw.parquet"
    
   
        file_exists = os.path.isfile(path)
    
        df.to_parquet(
            path, 
            engine="fastparquet", 
            append=file_exists  
        )
    
        print(f"Data saved to {path}")
        buffer = []