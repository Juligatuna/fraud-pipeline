from kafka import KafkaProducer
import json, time
from generator import generate_tx

producer = KafkaProducer(
    bootstrap_servers='localhost:9093',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

while True:
    tx = generate_tx()
    producer.send('transactions', value=tx)
    print(f"Sent transaction: {tx}")
    time.sleep(0.5)