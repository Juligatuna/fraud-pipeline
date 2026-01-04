import random, uuid, time, json, datetime
from faker import Faker

fake = Faker()

def generate_tx():
    txn = {
        "transaction_id": str(uuid.uuid4()),
        "customer_id": random.randint(1000, 9999),
        "timestamp": datetime.datetime.now().isoformat(),
        "amount": round(random.uniform(1, 2000), 2),
        "country": fake.country_code(),
        "merchant": fake.company(),
        "device_id": fake.uuid4(),
        "fraud": 1 if random.random() < 0.02 else 0  
    }
    return txn

if __name__ == "__main__":
    while True:
        print(json.dumps(generate_tx()))
        time.sleep(0.5)