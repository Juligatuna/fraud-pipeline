# 🕵️ Real-time Fraud Detection Pipeline
A production-ready system for detecting fraudulent banking transactions using real-time streaming, batch processing, and machine learning.

## 📋 Overview
This project simulates a complete fraud detection pipeline used by financial institutions. It generates realistic transaction data, processes it in real-time using Kafka, trains machine learning models to detect fraud, and provides monitoring through an interactive dashboard.

## 🎯 Key Features
- **Real-time Fraud Scoring:** ML model scores transactions as they flow through Kafka

- **Batch ETL Processing:** Apache Airflow pipeline for data cleaning and model retraining

- **Interactive Monitoring:** Streamlit dashboard with real-time metrics and visualizations

- **Data Warehouse:** PostgreSQL for historical analysis and reporting

- **Containerized Infrastructure:** Docker Compose for Kafka, Zookeeper, and PostgreSQL

## 🚀 Quick Start
Prerequisites
- Python 3.9+

- Docker & Docker Compose

- Git

## Installation
**Clone the repository**
```bash
git clone https://github.com/yourusername/fraud-pipeline.git
cd fraud-pipeline
```
**Create virtual environment and install dependencies**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Start infrastructure**
```bash
docker-compose up -d
```
**Wait for services to initialize**
```bash
sleep 30
```
**Initialize database**
```bash
 python services/database_setup.py
 ```
## Running the System
Open multiple terminal windows:

**Terminal 1 - Generate Transactions:**
```bash
python simulator/producer.py
```
**Terminal 2 - Real-time Fraud Detection:**
```bash
python services/scorer.py
```
**Terminal 3 - Launch Dashboard:**

```bash
streamlit run dashboard/fraud_dashboard.py --server.port 8501
```
**Terminal 4 - Start Airflow:**

```bash
# Initialize Airflow database
airflow db migrate

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

# Start Airflow services
airflow api-server --port 8080 &
airflow scheduler &
```
## 📊 Architecture
```bash
┌─────────────────┐    ┌─────────────┐    ┌─────────────────┐
│   Transaction   │    │   Kafka     │    │   Real-time     │
│   Generator     ├───►│   Broker    ├───►│   Scoring       │
│   (simulator/)  │    │  (Docker)   │    │  (scripts/)     │
└─────────────────┘    └─────────────┘    └────────┬────────┘
                                                    │
┌─────────────────┐    ┌─────────────┐    ┌────────▼────────┐
│   Airflow ETL   │    │ PostgreSQL  │    │   Dashboard     │
│   (airflow/)    ├───►│  (Docker)   │◄───┤   (dashboard/)  │
│   Model Training│    │             │    │                 │
└─────────────────┘    └─────────────┘    └─────────────────┘
```
## 📁 Project Structure
```bash
fraud-pipeline/
├── airflow/                    # Apache Airflow workflows
│   └── dags/
│       └── etl_clean_data.py  # ETL pipeline DAG
├── dashboard/                  # Streamlit dashboard
│   └── fraud_dashboard.py     # Real-time monitoring UI
├── data/                       # Data files
│   ├── raw.parquet           # Raw transaction data
│   ├── cleaned.parquet       # Cleaned data
│   └── warehouse_staging.csv # PostgreSQL staging file
├── docker-compose.yml          # Container orchestration
├── kafka/                      # Kafka configuration
├── model/                      # Machine Learning models
│   └── fraud.pkl             # Trained fraud detection model
├── notebooks/                  # Jupyter notebooks
│   └── train.ipynb           # Model training notebook
├── scripts/                    # Utility scripts
│   ├── consumer.py           # Kafka consumer for real-time scoring
│   └── database_test.py      # Database connection tests
├── services/                   # Service scripts
│   ├── database_setup.py     # Database initialization
│   └── scorer.py             # Real-time scoring service
├── simulator/                  # Transaction simulation
│   ├── generator.py          # Transaction data generator
│   └── producer.py           # Kafka producer
├── venv/                      # Python virtual environment
├── requirements.txt           # Python dependencies
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## 🔧 Components Explained
1. **Transaction Simulation (simulator/)**
- generator.py: Creates realistic banking transaction data

- producer.py: Publishes transactions to Kafka topic

2. **Real-time Processing (scripts/, services/)**
- consumer.py: Consumes Kafka messages, applies ML model for fraud detection

- scorer.py: Fraud scoring service using trained model

3. **Batch Processing (airflow/, notebooks/)**
- etl_clean_data.py: Airflow DAG for data cleaning, model training, and loading to PostgreSQL

- train.ipynb: Jupyter notebook for model training and experimentation

4. **Data Storage (services/)**
- database_setup.py: Initializes PostgreSQL database schema

- PostgreSQL: Stores processed transactions for historical analysis

5. **Monitoring & Visualization (dashboard/)**
fraud_dashboard.py: Interactive dashboard showing:

- Real-time transaction metrics

- Fraud detection statistics

- Geographic fraud distribution

- Merchant risk analysis

- Data export capabilities

## 📈 Machine Learning
**Model Training**
The fraud detection model is trained in notebooks/train.ipynb and the pipeline includes:

- Data preprocessing: Cleaning, normalization

- Feature engineering: Transaction amount analysis

- Model training: Random Forest classifier

- Evaluation: Accuracy, precision, recall metrics

**Model Deployment**
- Real-time: Model loaded by Kafka consumer for instant scoring

- Batch: Model retrained hourly via Airflow pipeline

- Persistence: Model saved as model/fraud.pkl

## 🛠️ Configuration
Environment Variables
Create a .env file:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=fraud_dw
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
KAFKA_BROKER=localhost:9093
Access Points
Dashboard: http://localhost:8501

Airflow UI: http://localhost:8080 (admin/admin)

PostgreSQL: psql -h localhost -p 5433 -U admin -d fraud_dw

Kafka: Broker at localhost:9093
```

## 🧪 Testing

**Test database connection**
 ```bash
 python scripts/database_test.py
```
**Test Kafka producer/consumer**
```bash
python simulator/producer.py --test
python scripts/consumer.py --test
```

**Trigger Airflow pipeline manually**
```bash
airflow dags trigger fraud_pipeline_v3
```
## 🤝 Contributing
Fork the repository

- Create a feature branch (git checkout -b feature/AmazingFeature)

- Commit your changes (git commit -m 'Add AmazingFeature')

- Push to the branch (git push origin feature/AmazingFeature)

- Open a Pull Request

## 📄 License
Distributed under the MIT License. See LICENSE for more information.

## 📬 Contact
Julius Irungu - 📧 juligatuna@gmail.com

Project Link: https://github.com/juligatuna/fraud-pipeline

## 🙏 Acknowledgments
- Apache Kafka for stream processing

- Apache Airflow for workflow orchestration

- Streamlit for dashboard creation

- PostgreSQL for data warehousing

- Scikit-learn for machine learning