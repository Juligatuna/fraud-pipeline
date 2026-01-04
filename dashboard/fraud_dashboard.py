import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from datetime import datetime, timedelta
import joblib
import numpy as np
from io import StringIO
import time

# Page config
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🕵️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
        margin-bottom: 1rem;
    }
    .fraud-alert {
        background-color: #FEE2E2;
        border-left: 5px solid #DC2626;
    }
</style>
""", unsafe_allow_html=True)

# Database connection with better management
def get_db_connection():
    """Create a new database connection each time"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            dbname="fraud_dw",
            user="admin",
            password="password",
            connect_timeout=10
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Load ML model
@st.cache_resource
def load_model():
    try:
        model = joblib.load("/home/julius-irungu/Desktop/Projects/fraud-pipeline/model/fraud.pkl")
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# Load data with proper connection management
def load_transaction_data():
    """Load data from PostgreSQL with fresh connection"""
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
        
        query = """
        SELECT 
            transaction_id::text,
            customer_id,
            timestamp,
            amount::float,
            country,
            merchant,
            fraud::int
        FROM transactions
        ORDER BY timestamp DESC
        LIMIT 100000
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            # Convert columns
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Header
st.markdown('<h1 class="main-header">🕵️ Fraud Detection Dashboard</h1>', unsafe_allow_html=True)
st.markdown("Real-time monitoring and ML-powered fraud detection")

# Load data
with st.spinner("Loading data from PostgreSQL..."):
    df = load_transaction_data()

model = load_model()

if df.empty:
    st.warning("No data available. Please run the Airflow pipeline first.")
    st.info("Run: `airflow dags trigger fraud_pipeline_v3`")
    st.stop()

# Initialize session state for filters
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = df.copy()

# Sidebar filters
st.sidebar.header("📊 Filters")

# Date range
if 'date' in df.columns:
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
    else:
        filtered_df = df.copy()
else:
    filtered_df = df.copy()

# Country filter
if 'country' in filtered_df.columns and not filtered_df.empty:
    countries = ['All'] + sorted(filtered_df['country'].dropna().unique().tolist())
    selected_country = st.sidebar.selectbox("Country", countries)
    
    if selected_country != 'All':
        filtered_df = filtered_df[filtered_df['country'] == selected_country]

# Amount filter
if 'amount' in filtered_df.columns and not filtered_df.empty:
    if filtered_df['amount'].notna().any():
        min_amount = float(filtered_df['amount'].min())
        max_amount = float(filtered_df['amount'].max())
        
        amount_range = st.sidebar.slider(
            "Amount Range ($)",
            min_value=min_amount,
            max_value=max_amount,
            value=(min_amount, max_amount),
            step=100.0
        )
        filtered_df = filtered_df[
            (filtered_df['amount'] >= amount_range[0]) & 
            (filtered_df['amount'] <= amount_range[1])
        ]

# Update session state
st.session_state.filtered_df = filtered_df

# Use filtered data for display
display_df = st.session_state.filtered_df

# Metrics
st.subheader("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_transactions = len(display_df)
    st.metric("Total Transactions", f"{total_transactions:,}")

with col2:
    fraud_count = display_df['fraud'].sum() if 'fraud' in display_df.columns else 0
    st.metric("Fraud Transactions", f"{fraud_count:,}")

with col3:
    fraud_rate = (fraud_count / total_transactions * 100) if total_transactions > 0 else 0
    st.metric("Fraud Rate", f"{fraud_rate:.2f}%")

with col4:
    if fraud_count > 0 and 'amount' in display_df.columns:
        avg_fraud_amount = display_df[display_df['fraud'] == 1]['amount'].mean()
        st.metric("Avg Fraud Amount", f"${avg_fraud_amount:,.2f}")
    else:
        st.metric("Avg Fraud Amount", "$0.00")

# Fraud alert
if fraud_count > 0:
    st.markdown(f"""
    <div class="metric-card fraud-alert">
        <h4>🚨 Fraud Alert</h4>
        <p>Detected <strong>{fraud_count}</strong> fraudulent transactions ({fraud_rate:.2f}% of total)</p>
        <p>Total fraud amount: <strong>${display_df[display_df['fraud'] == 1]['amount'].sum():,.2f}</strong></p>
    </div>
    """, unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🗺️ Geography", "🏪 Merchants", "📥 Export"])

with tab1:
    # Time series chart
    if not display_df.empty and 'date' in display_df.columns:
        daily_stats = display_df.groupby('date').agg(
            total=('transaction_id', 'count'),
            fraud=('fraud', 'sum')
        ).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily_stats['date'],
            y=daily_stats['total'],
            name='Total Transactions',
            marker_color='blue',
            opacity=0.7
        ))
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['fraud'],
            name='Fraud Transactions',
            mode='lines+markers',
            line=dict(color='red', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Daily Transaction Overview',
            xaxis_title='Date',
            yaxis_title='Count',
            hovermode='x unified',
            barmode='overlay'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Amount distribution
    if 'amount' in display_df.columns and not display_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                display_df, 
                x='amount',
                nbins=50,
                title='Transaction Amount Distribution',
                labels={'amount': 'Amount ($)', 'count': 'Count'},
                color_discrete_sequence=['blue']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Fraud by hour of day
            if fraud_count > 0 and 'hour' in display_df.columns:
                fraud_by_hour = display_df[display_df['fraud'] == 1].groupby('hour').size().reset_index(name='count')
                fig = px.line(
                    fraud_by_hour,
                    x='hour',
                    y='count',
                    title='Fraud Transactions by Hour of Day',
                    markers=True,
                    line_shape='spline'
                )
                st.plotly_chart(fig, use_container_width=True)

with tab2:  # Geography tab - FIXED
    st.header("🗺️ Geographic Analysis")
    
    if not display_df.empty and 'country' in display_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Fraud by country (top 10)
            if fraud_count > 0:
                fraud_by_country = display_df[display_df['fraud'] == 1].groupby('country').agg(
                    fraud_count=('fraud', 'sum'),
                    avg_amount=('amount', 'mean'),
                    total_amount=('amount', 'sum')
                ).reset_index()
                
                if not fraud_by_country.empty:
                    fraud_by_country = fraud_by_country.sort_values('fraud_count', ascending=False).head(10)
                    
                    fig = px.bar(
                        fraud_by_country,
                        x='country',
                        y='fraud_count',
                        title='Top 10 Countries by Fraud Count',
                        labels={'fraud_count': 'Fraud Count', 'country': 'Country'},
                        color='fraud_count',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No fraud data by country with current filters")
            else:
                st.info("No fraudulent transactions for geographic analysis")
        
        with col2:
            # Transaction volume by country
            if 'country' in display_df.columns:
                country_stats = display_df.groupby('country').agg(
                    transaction_count=('transaction_id', 'count'),
                    fraud_count=('fraud', 'sum')
                ).reset_index()
                
                country_stats['fraud_rate'] = (country_stats['fraud_count'] / country_stats['transaction_count'] * 100).round(2)
                country_stats = country_stats.sort_values('transaction_count', ascending=False).head(10)
                
                fig = px.bar(
                    country_stats,
                    x='country',
                    y='transaction_count',
                    title='Top 10 Countries by Transaction Volume',
                    labels={'transaction_count': 'Transaction Count', 'country': 'Country'},
                    color='transaction_count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Country data not available for geographic analysis")

with tab3:  # Merchants tab - FIXED
    st.header("🏪 Merchant Analysis")
    
    if not display_df.empty and 'merchant' in display_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top merchants by fraud
            if fraud_count > 0:
                fraud_by_merchant = display_df[display_df['fraud'] == 1].groupby('merchant').agg(
                    fraud_count=('fraud', 'sum'),
                    avg_amount=('amount', 'mean')
                ).reset_index()
                
                if not fraud_by_merchant.empty:
                    fraud_by_merchant = fraud_by_merchant.sort_values('fraud_count', ascending=False).head(10)
                    
                    fig = px.bar(
                        fraud_by_merchant,
                        x='merchant',
                        y='fraud_count',
                        title='Top 10 Merchants by Fraud Count',
                        labels={'fraud_count': 'Fraud Count', 'merchant': 'Merchant'},
                        color='fraud_count',
                        color_continuous_scale='Reds'
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No fraud data by merchant with current filters")
            else:
                st.info("No fraudulent transactions for merchant analysis")
        
        with col2:
            # Merchant risk analysis (fraud rate)
            if 'merchant' in display_df.columns and len(display_df) > 0:
                merchant_stats = display_df.groupby('merchant').agg(
                    transaction_count=('transaction_id', 'count'),
                    fraud_count=('fraud', 'sum')
                ).reset_index()
                
                # Calculate fraud rate only for merchants with sufficient transactions
                merchant_stats['fraud_rate'] = (merchant_stats['fraud_count'] / merchant_stats['transaction_count'] * 100).round(2)
                
                # Filter merchants with at least 5 transactions and sort by fraud rate
                risky_merchants = merchant_stats[
                    (merchant_stats['transaction_count'] >= 5) & 
                    (merchant_stats['fraud_count'] > 0)
                ].sort_values('fraud_rate', ascending=False).head(10)
                
                if not risky_merchants.empty:
                    fig = px.bar(
                        risky_merchants,
                        x='merchant',
                        y='fraud_rate',
                        title='Top 10 Risky Merchants (Fraud Rate %)',
                        labels={'fraud_rate': 'Fraud Rate (%)', 'merchant': 'Merchant'},
                        color='fraud_rate',
                        color_continuous_scale='Reds'
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No merchants with significant fraud rates")
    else:
        st.info("Merchant data not available for analysis")

with tab4:  # Export tab - FIXED
    st.header("📥 Data Export")
    
    # Get fresh data for export to avoid connection issues
    if st.button("🔄 Refresh Data for Export"):
        with st.spinner("Loading fresh data..."):
            export_df = load_transaction_data()
            if not export_df.empty:
                st.session_state.export_df = export_df
                st.success("Data refreshed successfully!")
            else:
                st.error("Failed to load data")
    
    # Use cached data or load fresh
    if 'export_df' not in st.session_state:
        export_df = display_df.copy()
    else:
        export_df = st.session_state.export_df.copy()
    
    # Apply filters to export data
    if not export_df.empty:
        # Apply the same filters as display
        if 'date' in export_df.columns and len(date_range) == 2:
            export_df = export_df[
                (export_df['date'] >= start_date) & 
                (export_df['date'] <= end_date)
            ]
        
        if selected_country != 'All' and 'country' in export_df.columns:
            export_df = export_df[export_df['country'] == selected_country]
        
        # Filter fraud transactions
        fraud_export_df = export_df[export_df['fraud'] == 1].copy()
        
        if not fraud_export_df.empty:
            st.subheader(f"Fraudulent Transactions ({len(fraud_export_df)} records)")
            
            # Show preview
            st.dataframe(
                fraud_export_df[['timestamp', 'amount', 'country', 'merchant', 'customer_id']]
                .sort_values('timestamp', ascending=False)
                .head(50),
                width='stretch'
            )
            
            # Download buttons - create fresh data each time
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV download with fresh connection
                if st.button("📥 Download as CSV", type="primary"):
                    try:
                        # Get fresh data for download
                        conn = get_db_connection()
                        if conn:
                            download_query = """
                            SELECT 
                                transaction_id::text,
                                customer_id,
                                timestamp,
                                amount::float,
                                country,
                                merchant,
                                fraud::int
                            FROM transactions
                            WHERE fraud = 1
                            ORDER BY timestamp DESC
                            """
                            download_df = pd.read_sql(download_query, conn)
                            conn.close()
                            
                            if not download_df.empty:
                                csv = download_df.to_csv(index=False)
                                st.download_button(
                                    label="Click to Save CSV",
                                    data=csv,
                                    file_name=f"fraud_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    key="csv_download"
                                )
                            else:
                                st.error("No fraud data to download")
                        else:
                            st.error("Could not connect to database")
                    except Exception as e:
                        st.error(f"Error downloading CSV: {e}")
            
            with col2:
                # JSON download
                if st.button("📥 Download as JSON"):
                    try:
                        conn = get_db_connection()
                        if conn:
                            download_query = """
                            SELECT 
                                transaction_id::text,
                                customer_id,
                                timestamp,
                                amount::float,
                                country,
                                merchant,
                                fraud::int
                            FROM transactions
                            WHERE fraud = 1
                            ORDER BY timestamp DESC
                            LIMIT 1000
                            """
                            download_df = pd.read_sql(download_query, conn)
                            conn.close()
                            
                            if not download_df.empty:
                                json_str = download_df.to_json(orient='records', date_format='iso')
                                st.download_button(
                                    label="Click to Save JSON",
                                    data=json_str,
                                    file_name=f"fraud_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json",
                                    key="json_download"
                                )
                            else:
                                st.error("No fraud data to download")
                        else:
                            st.error("Could not connect to database")
                    except Exception as e:
                        st.error(f"Error downloading JSON: {e}")
            
            # Summary
            st.subheader("Fraud Data Summary")
            if 'amount' in fraud_export_df.columns:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Fraud Amount", f"${fraud_export_df['amount'].sum():,.2f}")
                with col2:
                    st.metric("Average Fraud Amount", f"${fraud_export_df['amount'].mean():,.2f}")
                with col3:
                    st.metric("Max Fraud Amount", f"${fraud_export_df['amount'].max():,.2f}")
        else:
            st.info("No fraudulent transactions to export with current filters")
    else:
        st.warning("No data available for export")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: gray; font-size: 0.9rem;">
    <p>🕵️ Fraud Detection Dashboard • Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Data Source: PostgreSQL (localhost:5433) • Total Records: {len(display_df):,}</p>
</div>
""", unsafe_allow_html=True)