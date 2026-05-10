import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Carregar variáveis de ambiente
load_dotenv()

# ------------------------
# FUNÇÕES DE FORMATAÇÃO
# ------------------------
def format_currency(value):
    """Formata valor monetário em padrão BR"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def truncate_uuid(uuid_str):
    """Trunca UUID para mostrar só primeiros 8 caracteres"""
    return str(uuid_str)[:8] + "..."

def format_date_br(date):
    """Formata data no padrão BR"""
    return date.strftime("%d/%m/%Y")

# ------------------------
# CONFIG PAGE
# ------------------------
st.set_page_config(
    layout="wide",
    page_title="Financial Behavior Analytics",
    page_icon="📊"
)

# ------------------------
# DB CONNECTION
# ------------------------
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "finance_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )

@st.cache_data
def load_data():
    conn = get_connection()
    query = "SELECT * FROM mart_rfm"
    df = pd.read_sql(query, conn)
    df['last_transaction'] = pd.to_datetime(df['last_transaction'])
    conn.close()
    return df

# ------------------------
# LOAD DATA
# ------------------------
df = load_data()

# ------------------------
# HEADER
# ------------------------
st.title("📊 Financial Behavior Analytics")
st.markdown("### Dashboard RFM — Análise de Comportamento de Clientes")
st.markdown("---")

# ------------------------
# SIDEBAR (FILTROS)
# ------------------------
st.sidebar.title("🔎 Filtros")

# Filtro de segmento
segment_filter = st.sidebar.multiselect(
    "Segmento",
    options=sorted(df['segment'].unique()),
    default=df['segment'].unique()
)

# Filtro de período
min_date = df['last_transaction'].min().date()
max_date = df['last_transaction'].max().date()

date_range = st.sidebar.date_input(
    "Período",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Aplicar filtros
if len(date_range) == 2:
    df_filtered = df[
        (df['segment'].isin(segment_filter)) &
        (df['last_transaction'].dt.date >= date_range[0]) &
        (df['last_transaction'].dt.date <= date_range[1])
    ]
else:
    df_filtered = df[df['segment'].isin(segment_filter)]

# ------------------------
# KPIs
# ------------------------
col1, col2, col3, col4 = st.columns(4)

total_users = df_filtered['user_id'].nunique()
total_revenue = df_filtered['monetary'].sum()
avg_ticket = df_filtered['monetary'].mean()

# Cálculo de churn (inativo > 30 dias)
churn_threshold = datetime.now() - timedelta(days=30)
churn_count = len(df_filtered[df_filtered['last_transaction'] < churn_threshold])
churn_rate = (churn_count / total_users * 100) if total_users > 0 else 0

col1.metric("Clientes", f"{total_users:,}")
col2.metric("Receita Total", format_currency(total_revenue))
col3.metric("Ticket Médio", format_currency(avg_ticket))
col4.metric("Churn (%)", f"{churn_rate:.1f}%")

st.markdown("---")

# ------------------------
# VISUALIZAÇÕES PRINCIPAIS
# ------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Clientes por Segmento")
    
    segment_dist = df_filtered['segment'].value_counts().reset_index()
    segment_dist.columns = ['segment', 'count']
    
    fig1 = px.bar(
        segment_dist,
        x='segment',
        y='count',
        labels={'segment': 'Segmento', 'count': 'Quantidade'},
        color='segment',
        color_discrete_map={
            'VIP': '#2ecc71',
            'Ativo': '#3498db',
            'Regular': '#f39c12',
            'Risco de Churn': '#e74c3c'
        },
        text='count'
    )
    fig1.update_traces(textposition='outside')
    fig1.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("💰 Receita por Segmento")
    
    revenue_by_segment = df_filtered.groupby('segment')['monetary'].sum().reset_index()
    
    # Formatar valores para exibição
    revenue_by_segment['monetary_formatted'] = revenue_by_segment['monetary'].apply(
        lambda x: f"R$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    
    fig2 = px.bar(
        revenue_by_segment,
        x='segment',
        y='monetary',
        labels={'segment': 'Segmento', 'monetary': 'Receita (R$)'},
        color='segment',
        color_discrete_map={
            'VIP': '#2ecc71',
            'Ativo': '#3498db',
            'Regular': '#f39c12',
            'Risco de Churn': '#e74c3c'
        },
        text='monetary_formatted'
    )
    fig2.update_traces(textposition='outside')
    fig2.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ------------------------
# EVOLUÇÃO TEMPORAL
# ------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Evolução de Receita")
    
    time_series = df_filtered.copy()
    time_series['month'] = time_series['last_transaction'].dt.to_period('M').dt.to_timestamp()
    revenue_ts = time_series.groupby('month')['monetary'].sum().reset_index()
    
    fig3 = px.line(
        revenue_ts,
        x='month',
        y='monetary',
        labels={'month': 'Mês', 'monetary': 'Receita (R$)'},
        markers=True
    )
    fig3.update_traces(line_color='#3498db', line_width=3)
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("⚠️ Taxa de Churn ao Longo do Tempo")
    
    churn_df = df_filtered.copy()
    churn_df['month'] = churn_df['last_transaction'].dt.to_period('M').dt.to_timestamp()
    churn_df['is_churned'] = churn_df['last_transaction'] < churn_threshold
    
    churn_ts = churn_df.groupby('month').agg(
        total=('user_id', 'count'),
        churned=('is_churned', 'sum')
    ).reset_index()
    
    churn_ts['churn_rate'] = (churn_ts['churned'] / churn_ts['total'] * 100)
    
    fig4 = px.line(
        churn_ts,
        x='month',
        y='churn_rate',
        labels={'month': 'Mês', 'churn_rate': 'Taxa de Churn (%)'},
        markers=True
    )
    fig4.update_traces(line_color='#e74c3c', line_width=3)
    fig4.update_layout(height=400)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ------------------------
# DISTRIBUIÇÃO RFM
# ------------------------
st.subheader("🎯 Distribuição de Scores RFM")

col1, col2, col3 = st.columns(3)

with col1:
    fig5 = px.histogram(
        df_filtered,
        x='recency_score',
        title='Recency Score',
        labels={'recency_score': 'Score', 'count': 'Frequência'},
        color_discrete_sequence=['#3498db']
    )
    fig5.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)

with col2:
    fig6 = px.histogram(
        df_filtered,
        x='frequency_score',
        title='Frequency Score',
        labels={'frequency_score': 'Score', 'count': 'Frequência'},
        color_discrete_sequence=['#2ecc71']
    )
    fig6.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig6, use_container_width=True)

with col3:
    fig7 = px.histogram(
        df_filtered,
        x='monetary_score',
        title='Monetary Score',
        labels={'monetary_score': 'Score', 'count': 'Frequência'},
        color_discrete_sequence=['#f39c12']
    )
    fig7.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

# ------------------------
# ANÁLISE DETALHADA
# ------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 10 Clientes (Receita)")
    top_customers = df_filtered.nlargest(10, 'monetary')[
        ['user_id', 'name', 'segment', 'monetary', 'frequency', 'last_transaction']
    ].copy()
    
    # Formatação
    top_customers['user_id'] = top_customers['user_id'].apply(truncate_uuid)
    top_customers['monetary'] = top_customers['monetary'].apply(format_currency)
    top_customers['last_transaction'] = top_customers['last_transaction'].apply(format_date_br)
    
    st.dataframe(top_customers, use_container_width=True, hide_index=True)

with col2:
    st.subheader("⚠️ Risco de Churn (Prioridade)")
    churn_risk = df_filtered[df_filtered['segment'] == 'Risco de Churn'].nsmallest(10, 'last_transaction')[
        ['user_id', 'name', 'monetary', 'frequency', 'last_transaction']
    ].copy()
    
    # Formatação
    churn_risk['user_id'] = churn_risk['user_id'].apply(truncate_uuid)
    churn_risk['monetary'] = churn_risk['monetary'].apply(format_currency)
    churn_risk['last_transaction'] = churn_risk['last_transaction'].apply(format_date_br)
    
    st.dataframe(churn_risk, use_container_width=True, hide_index=True)

st.markdown("---")

# ------------------------
# SCATTER RFM
# ------------------------
st.subheader("🎯 Análise RFM — Scatter Plot")

# Criar colunas formatadas para hover
df_scatter = df_filtered.copy()
df_scatter['user_id_short'] = df_scatter['user_id'].apply(truncate_uuid)
df_scatter['monetary_fmt'] = df_scatter['monetary'].apply(format_currency)

fig8 = px.scatter(
    df_scatter,
    x='recency_score',
    y='monetary_score',
    size='frequency_score',
    color='segment',
    hover_data=['user_id_short', 'name', 'monetary_fmt'],
    labels={
        'recency_score': 'Recency Score',
        'monetary_score': 'Monetary Score',
        'frequency_score': 'Frequency Score',
        'user_id_short': 'User ID',
        'monetary_fmt': 'Receita'
    },
    color_discrete_map={
        'VIP': '#2ecc71',
        'Ativo': '#3498db',
        'Regular': '#f39c12',
        'Risco de Churn': '#e74c3c'
    }
)
fig8.update_layout(height=500)
st.plotly_chart(fig8, use_container_width=True)

st.markdown("---")

# ------------------------
# EXPORT
# ------------------------
st.subheader("⬇️ Exportar Dados")

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f"rfm_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

# ------------------------
# TABELA COMPLETA
# ------------------------
with st.expander("📋 Ver Base Completa de Dados"):
    df_display = df_filtered.copy()
    df_display['user_id'] = df_display['user_id'].apply(truncate_uuid)
    df_display['monetary'] = df_display['monetary'].apply(format_currency)
    df_display['last_transaction'] = df_display['last_transaction'].apply(format_date_br)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# ------------------------
# FOOTER
# ------------------------
st.markdown("---")
st.caption("Financial Behavior Analytics | Powered by dbt + Streamlit + PostgreSQL")