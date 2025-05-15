import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import hashlib
import networkx as nx
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
from pyvis.network import Network
import streamlit.components.v1 as components
import os
import json
import requests
from PIL import Image

# Set page configuration
st.set_page_config(layout="wide", page_title="Deteksi Pencucian Uang di Sektor Pertambangan")

# Initialize session state for login
if 'username' not in st.session_state:
    st.session_state['username'] = None

# Password hashing functions
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(password, hashed_password):
    return make_hash(password) == hashed_password

# Demo credentials
credentials = {
    "admin": make_hash("ppatk2025")  # Hashed password for 'ppatk2025'
}

# Logout function
def logout():
    st.session_state['username'] = None
    st.rerun()

# Sample data generation function
def load_sample_data():
    # Sample mining locations
    mining_locations = pd.DataFrame({
        'id': range(1, 11),
        'name': [f'Tambang {i}' for i in range(1, 11)],
        'district': ['Kabupaten A', 'Kabupaten B', 'Kabupaten C', 'Kabupaten D', 'Kabupaten E'] * 2,
        'province': ['Provinsi X'] * 5 + ['Provinsi Y'] * 5,
        'company': [f'PT Mining {chr(65+i)}' for i in range(10)],
        'license_type': ['IUP', 'IUPK', 'IUP', 'IUPK', 'IUP'] * 2,
        'commodity': ['Batubara', 'Emas', 'Tembaga', 'Nikel', 'Besi'] * 2,
        'area_2020': [1000, 1500, 1200, 2000, 1800, 1100, 1600, 1300, 1900, 1700],
        'area_2023': [1200, 1800, 1400, 2500, 2200, 1300, 1900, 1500, 2300, 2000],
        'land_change_anomaly': [0.2, 0.5, 0.3, 0.7, 0.6, 0.25, 0.45, 0.35, 0.65, 0.55],
        'lat': [-2.0, -2.5, -3.0, -3.5, -4.0, -2.2, -2.7, -3.2, -3.7, -4.2],
        'lon': [120.0, 120.5, 121.0, 121.5, 122.0, 120.2, 120.7, 121.2, 121.7, 122.2]
    })

    # Sample financial data
    financial_data = pd.DataFrame({
        'mine_id': range(1, 11),
        'reported_revenue': [1e9, 2e9, 1.5e9, 3e9, 2.5e9, 1.2e9, 2.2e9, 1.7e9, 2.8e9, 2.3e9],
        'estimated_production': [10000, 15000, 12000, 20000, 18000, 11000, 16000, 13000, 19000, 17000],
        'estimated_revenue': [1.2e9, 2.5e9, 1.8e9, 3.5e9, 3e9, 1.4e9, 2.7e9, 2e9, 3.3e9, 2.8e9],
        'tax_paid': [1e8, 2e8, 1.5e8, 3e8, 2.5e8, 1.2e8, 2.2e8, 1.7e8, 2.8e8, 2.3e8],
        'suspicious_score': [0.2, 0.5, 0.3, 0.7, 0.6, 0.25, 0.45, 0.35, 0.65, 0.55]
    })

    # Sample officials
    officials = pd.DataFrame({
        'id': range(1, 21),
        'name': [f'Pejabat {i}' for i in range(1, 21)],
        'position': ['Kepala Dinas', 'Bupati', 'Sekretaris', 'Anggota DPRD', 'Kepala Bidang'] * 4,
        'district': ['Kabupaten A', 'Kabupaten B', 'Kabupaten C', 'Kabupaten D', 'Kabupaten E'] * 4,
        'connected_mine_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 2,
        'connection_type': ['Pemilik', 'Investor', 'Konsultan', 'Tidak Ada', 'Pemegang Saham'] * 4,
        'risk_score': [0.3, 0.6, 0.4, 0.7, 0.5, 0.35, 0.65, 0.45, 0.75, 0.55] * 2
    })

    # Sample transactions
    transactions = []
    for i in range(100):
        official = officials.iloc[np.random.randint(0, len(officials))]
        date = pd.Timestamp('2022-01-01') + pd.Timedelta(days=np.random.randint(0, 730))
        risk_score = official['risk_score']
        is_suspicious = np.random.random() < risk_score

        if np.random.random() < 0.3:
            amount = np.random.choice([99000, 99900, 99990])
        else:
            amount = np.random.randint(5000, 100000)

        transaction_type = np.random.choice(
            ['Bank Transfer', 'E-Wallet', 'Cash Deposit', 'Property Purchase', 'Investment', 'Offshore Transfer'],
            p=[0.3, 0.2, 0.2, 0.1, 0.1, 0.1]
        )

        if transaction_type == 'Offshore Transfer' and is_suspicious:
            counterparty = np.random.choice(['Singapore Account', 'Hong Kong Account', 'Cayman Islands LLC'])
        elif transaction_type == 'Property Purchase' and is_suspicious:
            counterparty = 'Property Agent'
        elif transaction_type == 'Investment' and is_suspicious:
            counterparty = np.random.choice(['Mining Company', 'Shell Corporation', 'Family Business'])
        else:
            counterparty = np.random.choice(['Personal Account', 'Family Member', 'Local Business', 'Government Account'])

        frequency_pattern = np.random.random()
        structuring_pattern = np.random.random() if is_suspicious else np.random.random() * 0.3
        unusual_pattern = np.random.random() if is_suspicious else np.random.random() * 0.2

        ml_score = (frequency_pattern + structuring_pattern + unusual_pattern) / 3 * 0.7 + risk_score * 0.3
        flag = 'Suspicious' if ml_score > 0.6 or is_suspicious else 'Normal'

        transactions.append({
            'date': date,
            'official_id': official['id'],
            'official_name': official['name'],
            'position': official['position'],
            'district': official['district'],
            'amount': amount,
            'transaction_type': transaction_type,
            'counterparty': counterparty,
            'frequency_pattern': frequency_pattern,
            'structuring_pattern': structuring_pattern,
            'unusual_pattern': unusual_pattern,
            'ml_score': ml_score,
            'flag': flag,
            'connected_mine_id': official['connected_mine_id']
        })

    transactions_df = pd.DataFrame(transactions)

    # Sample connections
    connections = []
    for i in range(len(officials)):
        for j in range(i + 1, len(officials)):
            if officials.iloc[i]['district'] == officials.iloc[j]['district']:
                if np.random.random() < 0.7:
                    connections.append({
                        'source': officials.iloc[i]['name'],
                        'target': officials.iloc[j]['name'],
                        'weight': np.random.uniform(0.5, 1.0),
                        'type': 'Official-Official',
                        'description': 'Kolega di pemerintahan daerah'
                    })
            elif officials.iloc[i]['connected_mine_id'] == officials.iloc[j]['connected_mine_id']:
                if np.random.random() < 0.8:
                    connections.append({
                        'source': officials.iloc[i]['name'],
                        'target': officials.iloc[j]['name'],
                        'weight': np.random.uniform(0.6, 1.0),
                        'type': 'Official-Mine',
                        'description': 'Terlibat di tambang yang sama'
                    })
            else:
                if np.random.random() < 0.2:
                    connections.append({
                        'source': officials.iloc[i]['name'],
                        'target': officials.iloc[j]['name'],
                        'weight': np.random.uniform(0.1, 0.5),
                        'type': 'Official-Official',
                        'description': 'Koneksi umum'
                    })

    for i in range(len(officials)):
        mine_id = officials.iloc[i]['connected_mine_id']
        mine = mining_locations[mining_locations['id'] == mine_id].iloc[0]
        if officials.iloc[i]['connection_type'] != 'Tidak Ada':
            connections.append({
                'source': officials.iloc[i]['name'],
                'target': mine['company'],
                'weight': officials.iloc[i]['risk_score'],
                'type': 'Official-Company',
                'description': f"Koneksi {officials.iloc[i]['connection_type'].lower()}"
            })

    connections_df = pd.DataFrame(connections)

    # Land change analysis
    land_change = pd.DataFrame({
        'mine_id': mining_locations['id'],
        'name': mining_locations['name'],
        'district': mining_locations['district'],
        'area_2020': mining_locations['area_2020'],
        'area_2021': [round(mining_locations['area_2020'][i] + (mining_locations['area_2023'][i] - mining_locations['area_2020'][i]) * 0.3) for i in range(len(mining_locations))],
        'area_2022': [round(mining_locations['area_2020'][i] + (mining_locations['area_2023'][i] - mining_locations['area_2020'][i]) * 0.7) for i in range(len(mining_locations))],
        'area_2023': mining_locations['area_2023'],
        'percent_change': [(mining_locations['area_2023'][i] - mining_locations['area_2020'][i]) / mining_locations['area_2020'][i] * 100 for i in range(len(mining_locations))],
        'anomaly_score': mining_locations['land_change_anomaly'],
        'deforestation_impact': [round(np.random.uniform(0.5, 0.9) * (mining_locations['area_2023'][i] - mining_locations['area_2020'][i])) for i in range(len(mining_locations))],
        'water_impact': [round(np.random.uniform(0.3, 0.7) * (mining_locations['area_2023'][i] - mining_locations['area_2020'][i])) for i in range(len(mining_locations))],
        'license_compliance': [np.random.choice(['Sesuai', 'Tidak Sesuai', 'Perlu Verifikasi'], p=[0.4, 0.3, 0.3]) for _ in range(len(mining_locations))]
    })

    # Integrated risk assessment
    integrated_risk = pd.DataFrame({
        'mine_id': mining_locations['id'],
        'mine_name': mining_locations['name'],
        'district': mining_locations['district'],
        'land_change_risk': mining_locations['land_change_anomaly'],
        'financial_risk': financial_data['suspicious_score'],
        'official_risk': [officials[officials['connected_mine_id'] == mine_id]['risk_score'].mean() for mine_id in mining_locations['id']],
        'transaction_risk': [transactions_df[transactions_df['connected_mine_id'] == mine_id]['ml_score'].mean() for mine_id in mining_locations['id']],
    })

    integrated_risk['integrated_risk_score'] = (
        integrated_risk['land_change_risk'] * 0.25 +
        integrated_risk['financial_risk'] * 0.25 +
        integrated_risk['official_risk'] * 0.25 +
        integrated_risk['transaction_risk'] * 0.25
    )

    integrated_risk['risk_category'] = pd.cut(
        integrated_risk['integrated_risk_score'],
        bins=[0, 0.3, 0.6, 1.0],
        labels=['Rendah', 'Sedang', 'Tinggi']
    )

    return mining_locations, financial_data, officials, transactions_df, connections_df, land_change, integrated_risk

# Login page
def login_page():
    st.title("Login - Sistem Deteksi Pencucian Uang di Sektor Pertambangan")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Silakan masukkan kredensial Anda")
        st.markdown("""
        <style>
        div[data-testid="stForm"] {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username in credentials and check_password(password, credentials[username]):
                    st.session_state['username'] = username
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau password tidak valid")
        
        st.info("Demo credentials: Username: admin, Password: ppatk2025")

# Main application
def main_app():
    # Load data once
    mining_data, financial_data, officials, transactions, connections, land_change, integrated_risk = load_sample_data()

    # Create GeoJSON structure
    mining_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": row['id'],
                    "name": row['name'],
                    "district": row['district'],
                    "province": row['province'],
                    "company": row['company'],
                    "license_type": row['license_type'],
                    "commodity": row['commodity'],
                    "area_2020": row['area_2020'],
                    "area_2023": row['area_2023'],
                    "land_change_anomaly": row['land_change_anomaly']
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['lon'], row['lat']]
                }
            } for _, row in mining_data.iterrows()
        ]
    }

    # Sidebar navigation
    with st.sidebar:
        st.title("Navigasi")
        page = st.radio("Pilih Halaman", [
            "Dashboard Utama",
            "Analisis Perubahan Lahan",
            "Deteksi Transaksi Mencurigakan",
            "Analisis Jaringan Sosial",
            "Integrasi & Prediksi"
        ])
        if st.button("Logout"):
            logout()
        st.success(f"Login sebagai: {st.session_state['username']}")
        st.markdown("---")
        st.markdown("### Didukung oleh:")
        st.markdown("PPATK • OJK • ESDM")

    # Dashboard Utama
    if page == "Dashboard Utama":
        st.title("Dashboard Deteksi Pencucian Uang di Sektor Pertambangan")
        st.markdown("""
        Dashboard ini mengintegrasikan analisis perubahan lahan, transaksi keuangan, dan jaringan sosial
        untuk mendeteksi potensi pencucian uang oleh pejabat daerah dalam aktivitas pertambangan.
        """)

        # Key metrics
        st.subheader("Metrik Utama")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            high_risk_count = len(integrated_risk[integrated_risk['risk_category'] == 'Tinggi'])
            st.metric("Lokasi Risiko Tinggi", f"{high_risk_count}", f"{high_risk_count/len(integrated_risk)*100:.1f}%")
        with col2:
            suspicious_transactions = len(transactions[transactions['flag'] == 'Suspicious'])
            st.metric("Transaksi Mencurigakan", f"{suspicious_transactions}", f"{suspicious_transactions/len(transactions)*100:.1f}%")
        with col3:
            high_risk_officials = len(officials[officials['risk_score'] > 0.6])
            st.metric("Pejabat Berisiko Tinggi", f"{high_risk_officials}", f"{high_risk_officials/len(officials)*100:.1f}%")
        with col4:
            avg_land_change = land_change['percent_change'].mean()
            st.metric("Rata-rata Perubahan Lahan", f"{avg_land_change:.1f}%", "3 tahun terakhir")

        # Map visualization
        st.subheader("Peta Risiko Terintegrasi")
        m = folium.Map(location=[-2.5, 120], zoom_start=5, tiles="CartoDB positron")
        for _, row in integrated_risk.iterrows():
            mine_info = mining_data[mining_data['id'] == row['mine_id']].iloc[0]
            color = {'Tinggi': 'red', 'Sedang': 'orange', 'Rendah': 'green'}[row['risk_category']]
            popup_content = f"""
            <div style="width: 300px; font-family: Arial;">
                <h4 style="color: #333;">{mine_info['name']} ({mine_info['commodity']})</h4>
                <p><b>Kabupaten:</b> {mine_info['district']}</p>
                <p><b>Perusahaan:</b> {mine_info['company']}</p>
                <p><b>Izin:</b> {mine_info['license_type']}</p>
                <p><b>Perubahan Lahan:</b> {land_change[land_change['mine_id'] == row['mine_id']]['percent_change'].values[0]:.1f}%</p>
                <p><b>Skor Risiko:</b> {row['integrated_risk_score']:.2f} ({row['risk_category']})</p>
                <hr>
                <p><b>Risiko Perubahan Lahan:</b> {row['land_change_risk']:.2f}</p>
                <p><b>Risiko Keuangan:</b> {row['financial_risk']:.2f}</p>
                <p><b>Risiko Pejabat:</b> {row['official_risk']:.2f}</p>
                <p><b>Risiko Transaksi:</b> {row['transaction_risk']:.2f}</p>
            </div>
            """
            folium.CircleMarker(
                location=[mine_info['lat'], mine_info['lon']],
                radius=15,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_content, max_width=350)
            ).add_to(m)
            folium.Marker(
                location=[mine_info['lat'], mine_info['lon']],
                icon=folium.DivIcon(
                    icon_size=(100, 20),
                    icon_anchor=(50, 0),
                    html=f'<div style="font-size: 10pt; color: black; background-color: white; border-radius: 3px; padding: 2px 5px; opacity: 0.8;">{mine_info["name"]}</div>'
                )
            ).add_to(m)

        legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.3);">
            <p><b>Kategori Risiko:</b></p>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 15px; height: 15px; border-radius: 50%; background-color: red; margin-right: 5px;"></div>
                <span>Tinggi</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 15px; height: 15px; border-radius: 50%; background-color: orange; margin-right: 5px;"></div>
                <span>Sedang</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 15px; height: 15px; border-radius: 50%; background-color: green; margin-right: 5px;"></div>
                <span>Rendah</span>
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        folium_static(m, width=1200, height=500)

        # Risk distribution
        st.subheader("Distribusi Risiko")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(
                integrated_risk,
                names='risk_category',
                values=[1] * len(integrated_risk),
                color='risk_category',
                color_discrete_map={'Tinggi': 'red', 'Sedang': 'orange', 'Rendah': 'green'},
                title="Distribusi Kategori Risiko"
            )
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(
                integrated_risk.sort_values('integrated_risk_score', ascending=False),
                x='mine_name',
                y='integrated_risk_score',
                color='risk_category',
                color_discrete_map={'Tinggi': 'red', 'Sedang': 'orange', 'Rendah': 'green'},
                title="Skor Risiko Terintegrasi per Lokasi Tambang"
            )
            fig.update_layout(xaxis_title="Lokasi Tambang", yaxis_title="Skor Risiko")
            st.plotly_chart(fig, use_container_width=True)

        # Recent suspicious transactions
        st.subheader("Transaksi Mencurigakan Terbaru")
        recent_suspicious = transactions[transactions['flag'] == 'Suspicious'].sort_values('date', ascending=False).head(5)
        for _, tx in recent_suspicious.iterrows():
            with st.expander(f"{tx['official_name']} - Rp {tx['amount']:,.0f} - {tx['date'].strftime('%d %b %Y')}"):
                st.markdown(f"""
                **Pejabat:** {tx['official_name']} ({tx['position']})  
                **Kabupaten:** {tx['district']}  
                **Jumlah:** Rp {tx['amount']:,.0f}  
                **Jenis Transaksi:** {tx['transaction_type']}  
                **Pihak Terkait:** {tx['counterparty']}  
                **Skor ML:** {tx['ml_score']:.2f}  
                **Tambang Terkait:** {mining_data[mining_data['id'] == tx['connected_mine_id']]['name'].values[0]}
                """)

        # Risk factors correlation
        st.subheader("Korelasi Faktor Risiko")
        corr_data = integrated_risk[['land_change_risk', 'financial_risk', 'official_risk', 'transaction_risk']]
        corr_matrix = corr_data.corr()
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            color_continuous_scale='RdBu_r',
            title="Korelasi Antar Faktor Risiko"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Analisis Perubahan Lahan
    elif page == "Analisis Perubahan Lahan":
        st.title("Analisis Perubahan Lahan")
        st.markdown("""
        Halaman ini menampilkan analisis perubahan lahan pada lokasi tambang yang berpotensi
        mengindikasikan aktivitas pertambangan ilegal atau pencucian uang.
        """)

        # Land change map
        st.subheader("Peta Perubahan Lahan")
        col1, col2 = st.columns([3, 1])

        with col1:
            # Create base map
            m = folium.Map(location=[-2.5, 120], zoom_start=5, tiles="CartoDB positron")
            
            # Add time slider control
            year_options = {
                '2020': 'area_2020',
                '2021': 'area_2021', 
                '2022': 'area_2022',
                '2023': 'area_2023'
            }
            
            selected_year = st.select_slider(
                "Pilih Tahun untuk Visualisasi Lahan",
                options=list(year_options.keys()),
                value='2023'
            )
            
            area_column = year_options[selected_year]
            
            # Create choropleth map for selected year
            for _, row in land_change.iterrows():
                mine_info = mining_data[mining_data['id'] == row['mine_id']].iloc[0]
                
                # Calculate radius based on area for the selected year
                area_value = row[area_column]
                radius = max(5, min(25, area_value / 50))  # Scale radius based on area
                
                # Determine color based on growth rate compared to 2020
                if selected_year != '2020':
                    growth_rate = (row[area_column] - row['area_2020']) / row['area_2020'] * 100
                    if growth_rate > 50:
                        color = 'red'
                    elif growth_rate > 20:
                        color = 'orange'
                    else:
                        color = 'green'
                else:
                    color = 'blue'  # Base year
                
                # Create popup content
                popup_content = f"""
                <div style="width: 300px; font-family: Arial;">
                    <h4 style="color: #333;">{mine_info['name']} ({mine_info['commodity']})</h4>
                    <p><b>Kabupaten:</b> {mine_info['district']}</p>
                    <p><b>Perusahaan:</b> {mine_info['company']}</p>
                    <p><b>Luas {selected_year}:</b> {area_value} ha</p>
                    {f"<p><b>Perubahan dari 2020:</b> {growth_rate:.1f}%</p>" if selected_year != '2020' else ""}
                    <p><b>Kepatuhan Izin:</b> {row['license_compliance']}</p>
                    <p><b>Dampak Deforestasi:</b> {row['deforestation_impact']} ha</p>
                </div>
                """
                
                # Add circle marker
                folium.CircleMarker(
                    location=[mine_info['lat'], mine_info['lon']],
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_content, max_width=350)
                ).add_to(m)
                
                # Add label
                folium.Marker(
                    location=[mine_info['lat'], mine_info['lon']],
                    icon=folium.DivIcon(
                        icon_size=(100, 20),
                        icon_anchor=(50, 0),
                        html=f'<div style="font-size: 10pt; color: black; text-align: center;">{mine_info["name"]}</div>'
                    )
                ).add_to(m)
            
            # Add legend
            legend_html = """
            <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.3);">
                <p><b>Perubahan Lahan:</b></p>
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="width: 15px; height: 15px; border-radius: 50%; background-color: red; margin-right: 5px;"></div>
                    <span>Perubahan Tinggi (>50%)</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="width: 15px; height: 15px; border-radius: 50%; background-color: orange; margin-right: 5px;"></div>
                    <span>Perubahan Sedang (20-50%)</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="width: 15px; height: 15px; border-radius: 50%; background-color: green; margin-right: 5px;"></div>
                    <span>Perubahan Rendah (<20%)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 15px; height: 15px; border-radius: 50%; background-color: blue; margin-right: 5px;"></div>
                    <span>Tahun Dasar (2020)</span>
                </div>
                <p><i>Ukuran lingkaran menunjukkan luas area</i></p>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Display the map
            folium_static(m, width=800, height=500)

        with col2:
            # Add side panel with statistics
            st.subheader(f"Statistik {selected_year}")
            
            total_area = land_change[area_column].sum()
            st.metric("Total Luas Area", f"{total_area} ha")
            
            if selected_year != '2020':
                total_growth = ((land_change[area_column].sum() - land_change['area_2020'].sum()) / land_change['area_2020'].sum() * 100)
                st.metric("Pertumbuhan dari 2020", f"{total_growth:.1f}%")
                
                # Top growth locations
                st.subheader("Lokasi dengan Pertumbuhan Tertinggi")
                growth_data = land_change.copy()
                growth_data['growth_rate'] = (growth_data[area_column] - growth_data['area_2020']) / growth_data['area_2020'] * 100
                top_growth = growth_data.sort_values('growth_rate', ascending=False).head(3)
                
                for _, row in top_growth.iterrows():
                    st.markdown(f"**{row['name']}**: +{row['growth_rate']:.1f}% ({row['area_2020']} → {row[area_column]} ha)")

        # Land change analysis
        st.subheader("Analisis Perubahan Lahan (2020-2023)")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                land_change.sort_values('percent_change', ascending=False),
                x='name',
                y=['area_2020', 'area_2023'],
                barmode='group',
                title='Perbandingan Luas Area Tambang (hektar)',
                labels={'value': 'Luas (hektar)', 'name': 'Lokasi Tambang', 'variable': 'Tahun'},
                color_discrete_map={'area_2020': '#3498db', 'area_2023': '#e74c3c'}
            )
            fig.update_layout(xaxis_title="Lokasi Tambang", yaxis_title="Luas (hektar)")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(
                land_change.sort_values('percent_change', ascending=False),
                x='name',
                y='percent_change',
                title='Persentase Perubahan Lahan (2020-2023)',
                color='percent_change',
                color_continuous_scale=['green', 'yellow', 'red']
            )
            fig.update_layout(xaxis_title="Lokasi Tambang", yaxis_title="Perubahan (%)")
            st.plotly_chart(fig, use_container_width=True)

        # Time series analysis
        st.subheader("Analisis Deret Waktu Perubahan Lahan")
        time_series_data = []
        for _, row in land_change.iterrows():
            for year, area in [(2020, row['area_2020']), (2021, row['area_2021']), (2022, row['area_2022']), (2023, row['area_2023'])]:
                time_series_data.append({'name': row['name'], 'year': year, 'area': area})
        time_series_df = pd.DataFrame(time_series_data)
        selected_mines = st.multiselect(
            "Pilih Lokasi Tambang untuk Ditampilkan",
            options=land_change['name'].tolist(),
            default=land_change.sort_values('anomaly_score', ascending=False)['name'].head(3).tolist()
        )
        if selected_mines:
            filtered_ts = time_series_df[time_series_df['name'].isin(selected_mines)]
            fig = px.line(
                filtered_ts,
                x='year',
                y='area',
                color='name',
                title='Perubahan Luas Area Tambang dari Waktu ke Waktu',
                markers=True
            )
            fig.update_layout(xaxis_title="Tahun", yaxis_title="Luas (hektar)")
            st.plotly_chart(fig, use_container_width=True)

        # Environmental impact analysis
        st.subheader("Analisis Dampak Lingkungan")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                land_change.sort_values('deforestation_impact', ascending=False),
                x='name',
                y='deforestation_impact',
                title='Dampak Deforestasi (hektar)',
                color='deforestation_impact',
                color_continuous_scale=['green', 'yellow', 'red']
            )
            fig.update_layout(xaxis_title="Lokasi Tambang", yaxis_title="Area Deforestasi (hektar)")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(
                land_change.sort_values('water_impact', ascending=False),
                x='name',
                y='water_impact',
                title='Dampak pada Sumber Air (hektar)',
                color='water_impact',
                color_continuous_scale=['blue', 'purple', 'red']
            )
            fig.update_layout(xaxis_title="Lokasi Tambang", yaxis_title="Area Dampak Air (hektar)")
            st.plotly_chart(fig, use_container_width=True)

        # License compliance analysis
        st.subheader("Analisis Kepatuhan Izin")
        compliance_counts = land_change['license_compliance'].value_counts().reset_index()
        compliance_counts.columns = ['Status', 'Count']
        fig = px.pie(
            compliance_counts,
            values='Count',
            names='Status',
            title='Distribusi Status Kepatuhan Izin',
            color='Status',
            color_discrete_map={'Sesuai': 'green', 'Tidak Sesuai': 'red', 'Perlu Verifikasi': 'orange'}
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        # Anomaly detection model
        st.subheader("Model Deteksi Anomali Perubahan Lahan")
        X = land_change[['percent_change', 'deforestation_impact', 'water_impact']].copy()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = IsolationForest(contamination=0.3, random_state=42)
        model.fit(X_scaled)
        anomaly_scores = -model.score_samples(X_scaled)
        land_change['model_anomaly_score'] = anomaly_scores
        land_change['model_anomaly'] = model.predict(X_scaled)
        land_change['model_anomaly'] = land_change['model_anomaly'].map({1: 'Normal', -1: 'Anomali'})
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.scatter(
                land_change,
                x='percent_change',
                y='model_anomaly_score',
                color='model_anomaly',
                hover_name='name',
                title='Skor Anomali Model vs Persentase Perubahan',
                color_discrete_map={'Normal': 'blue', 'Anomali': 'red'}
            )
            fig.update_layout(xaxis_title="Persentase Perubahan", yaxis_title="Skor Anomali Model")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(
                land_change,
                x='deforestation_impact',
                y='water_impact',
                size='percent_change',
                color='model_anomaly',
                hover_name='name',
                title='Dampak Deforestasi vs Dampak Air',
                color_discrete_map={'Normal': 'blue', 'Anomali': 'red'}
            )
            fig.update_layout(xaxis_title="Dampak Deforestasi (ha)", yaxis_title="Dampak Air (ha)")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Hasil Deteksi Anomali")
        anomalies = land_change[land_change['model_anomaly'] == 'Anomali'].sort_values('model_anomaly_score', ascending=False)
        if not anomalies.empty:
            st.markdown(f"**Terdeteksi {len(anomalies)} lokasi tambang dengan anomali perubahan lahan:**")
            for _, row in anomalies.iterrows():
                with st.expander(f"{row['name']} - Skor Anomali: {row['model_anomaly_score']:.2f}"):
                    st.markdown(f"""
                    **Lokasi:** {row['name']} ({row['district']})  
                    **Perubahan Lahan:** {row['percent_change']:.1f}% (2020: {row['area_2020']} ha → 2023: {row['area_2023']} ha)  
                    **Dampak Deforestasi:** {row['deforestation_impact']} ha  
                    **Dampak Air:** {row['water_impact']} ha  
                    **Kepatuhan Izin:** {row['license_compliance']}  
                    **Skor Anomali Model:** {row['model_anomaly_score']:.2f}
                    """)
                    connected_officials = officials[officials['connected_mine_id'] == row['mine_id']]
                    if not connected_officials.empty:
                        st.markdown("**Pejabat Terkait:**")
                        for _, official in connected_officials.iterrows():
                            st.markdown(f"- {official['name']} ({official['position']}) - Skor Risiko: {official['risk_score']:.2f}")
        else:
            st.info("Tidak ada anomali perubahan lahan yang terdeteksi.")

    # Deteksi Transaksi Mencurigakan
    elif page == "Deteksi Transaksi Mencurigakan":
        st.title("Deteksi Transaksi Keuangan Mencurigakan")
        st.markdown("""
        Halaman ini menampilkan analisis transaksi keuangan pejabat daerah yang berpotensi
        terkait dengan aktivitas pencucian uang di sektor pertambangan.
        """)

        st.subheader("Ringkasan Transaksi")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_transactions = len(transactions)
            st.metric("Total Transaksi", f"{total_transactions:,}")
        with col2:
            suspicious_count = len(transactions[transactions['flag'] == 'Suspicious'])
            st.metric("Transaksi Mencurigakan", f"{suspicious_count:,}", f"{suspicious_count/total_transactions*100:.1f}%")
        with col3:
            total_amount = transactions['amount'].sum()
            st.metric("Total Nilai Transaksi", f"Rp {total_amount:,.0f}")
        with col4:
            suspicious_amount = transactions[transactions['flag'] == 'Suspicious']['amount'].sum()
            st.metric("Nilai Transaksi Mencurigakan", f"Rp {suspicious_amount:,.0f}", f"{suspicious_amount/total_amount*100:.1f}%")

        st.subheader("Filter Transaksi")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_districts = st.multiselect("Kabupaten", options=sorted(transactions['district'].unique()), default=[])
        with col2:
            selected_positions = st.multiselect("Jabatan", options=sorted(transactions['position'].unique()), default=[])
        with col3:
            selected_types = st.multiselect("Jenis Transaksi", options=sorted(transactions['transaction_type'].unique()), default=[])
        date_range = st.slider(
            "Rentang Tanggal",
            min_value=transactions['date'].min().date(),
            max_value=transactions['date'].max().date(),
            value=(transactions['date'].min().date(), transactions['date'].max().date())
        )

        filtered_transactions = transactions.copy()
        if selected_districts:
            filtered_transactions = filtered_transactions[filtered_transactions['district'].isin(selected_districts)]
        if selected_positions:
            filtered_transactions = filtered_transactions[filtered_transactions['position'].isin(selected_positions)]
        if selected_types:
            filtered_transactions = filtered_transactions[filtered_transactions['transaction_type'].isin(selected_types)]
        filtered_transactions = filtered_transactions[
            (filtered_transactions['date'].dt.date >= date_range[0]) &
            (filtered_transactions['date'].dt.date <= date_range[1])
        ]

        st.subheader("Analisis Transaksi")
        col1, col2 = st.columns(2)
        with col1:
            tx_by_type = filtered_transactions.groupby('transaction_type')['amount'].sum().reset_index()
            fig = px.pie(tx_by_type, values='amount', names='transaction_type', title='Distribusi Nilai Transaksi berdasarkan Jenis', hole=0.4)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            tx_by_flag = filtered_transactions.groupby('flag')['amount'].sum().reset_index()
            fig = px.pie(
                tx_by_flag,
                values='amount',
                names='flag',
                title='Distribusi Nilai Transaksi berdasarkan Flag',
                color='flag',
                color_discrete_map={'Normal': 'green', 'Suspicious': 'red'},
                hole=0.4
            )
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Timeline Transaksi")
        timeline_data = filtered_transactions.groupby([pd.Grouper(key='date', freq='M'), 'flag'])['amount'].sum().reset_index()
        fig = px.line(
            timeline_data,
            x='date',
            y='amount',
            color='flag',
            title='Nilai Transaksi per Bulan',
            color_discrete_map={'Normal': 'green', 'Suspicious': 'red'}
        )
        fig.update_layout(xaxis_title="Tanggal", yaxis_title="Nilai Transaksi (Rp)")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Pejabat dengan Transaksi Mencurigakan")
        suspicious_by_official = filtered_transactions[filtered_transactions['flag'] == 'Suspicious'].groupby('official_name').agg(
            total_suspicious=('amount', 'sum'),
            count_suspicious=('amount', 'count'),
            avg_ml_score=('ml_score', 'mean')
        ).reset_index().sort_values('total_suspicious', ascending=False)
        if not suspicious_by_official.empty:
            fig = px.bar(
                suspicious_by_official.head(10),
                x='official_name',
                y='total_suspicious',
                color='avg_ml_score',
                title='Top 10 Pejabat berdasarkan Nilai Transaksi Mencurigakan',
                color_continuous_scale=['yellow', 'orange', 'red'],
                text='count_suspicious'
            )
            fig.update_layout(
                xaxis_title="Nama Pejabat",
                yaxis_title="Total Nilai Transaksi Mencurigakan (Rp)",
                coloraxis_colorbar_title="Rata-rata Skor ML"
            )
            fig.update_traces(texttemplate='%{text} tx', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada transaksi mencurigakan yang terdeteksi dengan filter yang dipilih.")

        st.subheader("Pola Transaksi Mencurigakan")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(
                filtered_transactions,
                x='amount',
                color='flag',
                marginal='box',
                title='Distribusi Nilai Transaksi',
                color_discrete_map={'Normal': 'green', 'Suspicious': 'red'},
                nbins=50
            )
            fig.update_layout(xaxis_title="Nilai Transaksi (Rp)", yaxis_title="Jumlah Transaksi")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.histogram(
                filtered_transactions,
                x='ml_score',
                color='flag',
                marginal='box',
                title='Distribusi Skor ML',
                color_discrete_map={'Normal': 'green', 'Suspicious': 'red'},
                nbins=50
            )
            fig.update_layout(xaxis_title="Skor ML", yaxis_title="Jumlah Transaksi")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Tabel Transaksi Terfilter")
        display_transactions = filtered_transactions.copy()
        display_transactions['date'] = display_transactions['date'].dt.strftime('%d %b %Y')
        display_transactions['amount'] = display_transactions['amount'].apply(lambda x: f"Rp {x:,.0f}")
        display_transactions['ml_score'] = display_transactions['ml_score'].apply(lambda x: f"{x:.2f}")
        display_columns = ['date', 'official_name', 'position', 'district', 'amount', 'transaction_type', 'counterparty', 'ml_score', 'flag']
        st.dataframe(
            display_transactions[display_columns].style.apply(
                lambda x: ['background-color: #ffcccc' if x['flag'] == 'Suspicious' else '' for i in x],
                axis=1
            ),
            height=400
        )

        st.subheader("Penjelasan Model Machine Learning")
        st.markdown("""
        Model deteksi transaksi mencurigakan menggunakan kombinasi dari beberapa fitur:
        
        1. **Pola Frekuensi** - Mengidentifikasi transaksi berulang dengan pola tidak wajar
        2. **Pola Strukturisasi** - Mendeteksi upaya memecah transaksi besar menjadi transaksi kecil
        3. **Pola Tidak Biasa** - Menganalisis transaksi yang tidak sesuai dengan perilaku normal
        
        Model ini juga mempertimbangkan profil risiko pejabat berdasarkan jabatan dan koneksi dengan tambang.
        """)
        feature_importance = pd.DataFrame({
            'Feature': ['Pola Frekuensi', 'Pola Strukturisasi', 'Pola Tidak Biasa', 'Skor Risiko Pejabat'],
            'Importance': [0.25, 0.30, 0.25, 0.20]
        })
        fig = px.bar(
            feature_importance,
            x='Feature',
            y='Importance',
            title='Kepentingan Fitur dalam Model ML',
            color='Importance',
            color_continuous_scale=['blue', 'purple', 'red']
        )
        st.plotly_chart(fig, use_container_width=True)

    # Analisis Jaringan Sosial
    elif page == "Analisis Jaringan Sosial":
        st.title("Analisis Jaringan Sosial")
        st.markdown("""
        Halaman ini menampilkan analisis jaringan sosial antara pejabat daerah dan perusahaan tambang
        untuk mengidentifikasi potensi konflik kepentingan dan jaringan pencucian uang.
        """)

        st.subheader("Visualisasi Jaringan")
        
        # Create a networkx graph first
        G = nx.Graph()
        for _, official in officials.iterrows():
            G.add_node(official['name'], type='Official', position=official['position'], district=official['district'], risk_score=official['risk_score'])
        for _, mine in mining_data.iterrows():
            G.add_node(mine['company'], type='Company', commodity=mine['commodity'], district=mine['district'], license_type=mine['license_type'])
        for _, conn in connections.iterrows():
            G.add_edge(conn['source'], conn['target'], weight=conn['weight'], type=conn['type'], description=conn['description'])
        
        try:
            # Try to use pyvis Network
            from pyvis.network import Network
            net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
            net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=250, spring_strength=0.001, damping=0.09)
            
            # Add nodes and edges
            for node in G.nodes(data=True):
                node_name, node_attrs = node
                if node_attrs['type'] == 'Official':
                    color = '#e74c3c' if node_attrs['risk_score'] > 0.6 else '#f39c12' if node_attrs['risk_score'] > 0.3 else '#3498db'
                    title = f"Pejabat: {node_name}<br>Jabatan: {node_attrs['position']}<br>Kabupaten: {node_attrs['district']}<br>Skor Risiko: {node_attrs['risk_score']:.2f}"
                    net.add_node(node_name, title=title, color=color, size=20, shape='circle')
                else:
                    title = f"Perusahaan: {node_name}<br>Komoditas: {node_attrs['commodity']}<br>Kabupaten: {node_attrs['district']}<br>Jenis Izin: {node_attrs['license_type']}"
                    net.add_node(node_name, title=title, color='#2ecc71', size=25, shape='square')
            
            for edge in G.edges(data=True):
                source, target, edge_attrs = edge
                width = edge_attrs['weight'] * 5
                color = '#e74c3c' if edge_attrs['type'] == 'Official-Company' else '#95a5a6'
                net.add_edge(source, target, title=edge_attrs['description'], width=width, color=color)
            
            # Save and display
            net.save_graph("network.html")
            with open("network.html", "r", encoding="utf-8") as f:
                components.html(f.read(), height=600)
                
        except (ImportError, NameError) as e:
            # Fallback to a simple networkx visualization if pyvis is not available
            st.error(f"Tidak dapat memuat visualisasi jaringan interaktif. Error: {str(e)}")
            st.info("Menampilkan visualisasi jaringan sederhana sebagai alternatif.")
            
            # Create a simple matplotlib visualization
            plt.figure(figsize=(10, 8))
            pos = nx.spring_layout(G, seed=42)
            
            # Draw nodes
            official_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'Official']
            company_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'Company']
            
            nx.draw_networkx_nodes(G, pos, nodelist=official_nodes, node_color='#3498db', node_size=300, label='Pejabat')
            nx.draw_networkx_nodes(G, pos, nodelist=company_nodes, node_color='#2ecc71', node_size=500, label='Perusahaan')
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, width=1, alpha=0.7)
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=8)
            
            plt.title("Jaringan Sosial Pejabat dan Perusahaan Tambang")
            plt.legend()
            plt.axis('off')
            st.pyplot(plt)

        st.subheader("Metrik Jaringan")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Jumlah Node", len(G.nodes()))
        with col2:
            st.metric("Jumlah Edge", len(G.edges()))
        with col3:
            density = nx.density(G)
            st.metric("Densitas Jaringan", f"{density:.3f}")
        with col4:
            avg_clustering = nx.average_clustering(G)
            st.metric("Koefisien Clustering", f"{avg_clustering:.3f}")

        st.subheader("Analisis Sentralitas")
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
        centrality_df = pd.DataFrame({
            'Node': list(degree_centrality.keys()),
            'Degree Centrality': list(degree_centrality.values()),
            'Betweenness Centrality': list(betweenness_centrality.values()),
            'Eigenvector Centrality': list(eigenvector_centrality.values())
        })
        centrality_df['Type'] = centrality_df['Node'].apply(lambda x: 'Official' if x in officials['name'].values else 'Company')
        risk_scores = {official['name']: official['risk_score'] for _, official in officials.iterrows()}
        centrality_df['Risk Score'] = centrality_df['Node'].apply(lambda x: risk_scores.get(x, 0) if x in officials['name'].values else 0)
        centrality_df = centrality_df.sort_values('Degree Centrality', ascending=False)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.scatter(
                centrality_df,
                x='Degree Centrality',
                y='Betweenness Centrality',
                color='Type',
                size='Risk Score',
                hover_name='Node',
                title='Degree vs Betweenness Centrality',
                color_discrete_map={'Official': '#3498db', 'Company': '#2ecc71'}
            )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(
                centrality_df,
                x='Degree Centrality',
                y='Eigenvector Centrality',
                color='Type',
                size='Risk Score',
                hover_name='Node',
                title='Degree vs Eigenvector Centrality',
                color_discrete_map={'Official': '#3498db', 'Company': '#2ecc71'}
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Node Paling Berpengaruh")
        centrality_df['Influence Score'] = (
            centrality_df['Degree Centrality'] * 0.3 +
            centrality_df['Betweenness Centrality'] * 0.4 +
            centrality_df['Eigenvector Centrality'] * 0.3
        )
        top_influential = centrality_df.sort_values('Influence Score', ascending=False).head(10)
        fig = px.bar(
            top_influential,
            x='Node',
            y='Influence Score',
            color='Type',
            title='Top 10 Node Paling Berpengaruh',
            color_discrete_map={'Official': '#3498db', 'Company': '#2ecc71'}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Deteksi Komunitas")
        communities = nx.community.louvain_communities(G)
        community_data = []
        for i, community in enumerate(communities):
            for node in community:
                node_type = 'Official' if node in officials['name'].values else 'Company'
                community_data.append({'Node': node, 'Community': f"Komunitas {i+1}", 'Type': node_type})
        community_df = pd.DataFrame(community_data)
        community_size = community_df.groupby('Community').size().reset_index(name='Size')
        fig = px.bar(community_size, x='Community', y='Size', title='Ukuran Komunitas', color='Community')
        st.plotly_chart(fig, use_container_width=True)

        community_composition = community_df.groupby(['Community', 'Type']).size().reset_index(name='Count')
        fig = px.bar(
            community_composition,
            x='Community',
            y='Count',
            color='Type',
            title='Komposisi Komunitas',
            barmode='group',
            color_discrete_map={'Official': '#3498db', 'Company': '#2ecc71'}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Analisis Risiko berdasarkan Komunitas")
        community_risk = community_df.copy()
        community_risk['Risk Score'] = community_risk['Node'].apply(lambda x: risk_scores.get(x, 0) if x in officials['name'].values else 0)
        community_avg_risk = community_risk[community_risk['Type'] == 'Official'].groupby('Community')['Risk Score'].mean().reset_index()
        fig = px.bar(
            community_avg_risk,
            x='Community',
            y='Risk Score',
            title='Rata-rata Skor Risiko Pejabat per Komunitas',
            color='Risk Score',
            color_continuous_scale=['green', 'yellow', 'red']
        )
        st.plotly_chart(fig, use_container_width=True)

    # Integrasi & Prediksi
    elif page == "Integrasi & Prediksi":
        st.title("Integrasi & Prediksi")
        st.markdown("""
        Halaman ini menampilkan analisis integrasi risiko dan model prediktif untuk
        mendeteksi potensi pencucian uang di sektor pertambangan.
        """)

        selected_mine = st.selectbox("Pilih Lokasi Tambang", options=integrated_risk['mine_name'].unique(), index=0)
        mine_data = integrated_risk[integrated_risk['mine_name'] == selected_mine].iloc[0]

        st.subheader("Informasi Lokasi Tambang")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nama Lokasi", mine_data['mine_name'])
            st.metric("Kabupaten", mine_data['district'])
        with col2:
            st.metric("Skor Risiko Terintegrasi", f"{mine_data['integrated_risk_score']:.2f}")
            st.metric("Kategori Risiko", mine_data['risk_category'])
        with col3:
            st.metric("Risiko Perubahan Lahan", f"{mine_data['land_change_risk']:.2f}")
            st.metric("Risiko Keuangan", f"{mine_data['financial_risk']:.2f}")

        st.subheader("Pejabat Terkait")
        connected_officials = officials[officials['connected_mine_id'] == mine_data['mine_id']]
        if not connected_officials.empty:
            st.dataframe(connected_officials[['name', 'position', 'district', 'risk_score']])
        else:
            st.info(f"Tidak ada pejabat yang terkait dengan {selected_mine}")

        st.subheader("Model Prediktif Risiko Pencucian Uang")
        X = integrated_risk[['land_change_risk', 'financial_risk', 'official_risk', 'transaction_risk']].values
        y = integrated_risk['risk_category'].map({'Rendah': 0, 'Sedang': 1, 'Tinggi': 2}).values
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        feature_importance = pd.DataFrame({
            'Feature': ['Perubahan Lahan', 'Keuangan', 'Pejabat', 'Transaksi'],
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=False)
        fig = px.bar(
            feature_importance,
            x='Feature',
            y='Importance',
            title='Kepentingan Fitur dalam Model Prediktif',
            color='Importance',
            color_continuous_scale=['blue', 'purple', 'red']
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Analisis What-If")
        st.markdown("Gunakan slider di bawah untuk menyesuaikan faktor risiko dan melihat prediksi risiko.")
        col1, col2 = st.columns(2)
        with col1:
            new_land = st.slider("Risiko Perubahan Lahan", 0.0, 1.0, float(mine_data['land_change_risk']), step=0.01)
            new_financial = st.slider("Risiko Keuangan", 0.0, 1.0, float(mine_data['financial_risk']), step=0.01)
        with col2:
            new_official = st.slider("Risiko Pejabat", 0.0, 1.0, float(mine_data['official_risk']), step=0.01)
            new_transaction = st.slider("Risiko Transaksi", 0.0, 1.0, float(mine_data['transaction_risk']), step=0.01)

        new_integrated_score = (new_land * 0.25 + new_financial * 0.25 + new_official * 0.25 + new_transaction * 0.25)
        new_features = np.array([[new_land, new_financial, new_official, new_transaction]])
        predicted_category_idx = model.predict(new_features)[0]
        predicted_category = ['Rendah', 'Sedang', 'Tinggi'][predicted_category_idx]
        probabilities = model.predict_proba(new_features)[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Skor Risiko Terintegrasi Baru", f"{new_integrated_score:.2f}", f"{new_integrated_score - mine_data['integrated_risk_score']:.2f}")
        with col2:
            st.metric("Kategori Risiko Saat Ini", mine_data['risk_category'])
        with col3:
            st.metric("Kategori Risiko Prediksi", predicted_category)

        prob_data = pd.DataFrame({'Category': ['Rendah', 'Sedang', 'Tinggi'], 'Probability': probabilities})
        fig = px.bar(
            prob_data,
            x='Category',
            y='Probability',
            title='Probabilitas Kategori Risiko',
            color='Category',
            color_discrete_map={'Rendah': 'green', 'Sedang': 'orange', 'Tinggi': 'red'}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Rekomendasi Tindakan")
        if predicted_category == 'Tinggi':
            st.error("""
            ### Risiko Tinggi - Tindakan Segera Diperlukan
            **Rekomendasi:**
            1. Lakukan audit menyeluruh terhadap operasi tambang dan keuangan perusahaan
            2. Investigasi transaksi keuangan mencurigakan yang terkait dengan pejabat
            3. Verifikasi kepatuhan izin dan legalitas perubahan lahan
            4. Koordinasi dengan KPK untuk penyelidikan lebih lanjut
            """)
        elif predicted_category == 'Sedang':
            st.warning("""
            ### Risiko Sedang - Perlu Pengawasan Lebih Ketat
            **Rekomendasi:**
            1. Tingkatkan pengawasan terhadap operasi tambang
            2. Lakukan verifikasi laporan keuangan dan pembayaran pajak
            3. Monitor transaksi keuangan pejabat yang terkait
            4. Evaluasi kepatuhan terhadap regulasi lingkungan
            """)
        else:
            st.success("""
            ### Risiko Rendah - Tetap Waspada
            **Rekomendasi:**
            1. Lanjutkan pemantauan rutin
            2. Verifikasi laporan periodik
            3. Pastikan kepatuhan terhadap regulasi yang berlaku
            """)

        st.subheader("Simulasi Intervensi")
        intervention_options = [
            "Audit Keuangan Menyeluruh",
            "Verifikasi Izin Tambang",
            "Investigasi Pejabat Terkait",
            "Pemantauan Transaksi",
            "Evaluasi Dampak Lingkungan"
        ]
        selected_interventions = st.multiselect("Pilih Intervensi yang Akan Diterapkan", options=intervention_options)
        if selected_interventions:
            intervention_effects = {
                "Audit Keuangan Menyeluruh": {'financial': -0.3, 'transaction': -0.2},
                "Verifikasi Izin Tambang": {'land': -0.25, 'official': -0.1},
                "Investigasi Pejabat Terkait": {'official': -0.4, 'transaction': -0.2},
                "Pemantauan Transaksi": {'transaction': -0.35},
                "Evaluasi Dampak Lingkungan": {'land': -0.3}
            }
            sim_land, sim_financial, sim_official, sim_transaction = new_land, new_financial, new_official, new_transaction
            for intervention in selected_interventions:
                effects = intervention_effects[intervention]
                if 'land' in effects:
                    sim_land = max(0, sim_land + effects['land'])
                if 'financial' in effects:
                    sim_financial = max(0, sim_financial + effects['financial'])
                if 'official' in effects:
                    sim_official = max(0, sim_official + effects['official'])
                if 'transaction' in effects:
                    sim_transaction = max(0, sim_transaction + effects['transaction'])
            
            post_intervention_score = (sim_land * 0.25 + sim_financial * 0.25 + sim_official * 0.25 + sim_transaction * 0.25)
            post_features = np.array([[sim_land, sim_financial, sim_official, sim_transaction]])
            post_category_idx = model.predict(post_features)[0]
            post_category = ['Rendah', 'Sedang', 'Tinggi'][post_category_idx]
            
            st.subheader("Hasil Simulasi Intervensi")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Skor Risiko Sebelum Intervensi", f"{new_integrated_score:.2f}")
                st.metric("Kategori Risiko Sebelum Intervensi", predicted_category)
            with col2:
                st.metric("Skor Risiko Setelah Intervensi", f"{post_intervention_score:.2f}")
                st.metric("Kategori Risiko Setelah Intervensi", post_category)

# Run the app
if st.session_state['username'] is None:
    login_page()
else:
    main_app()
