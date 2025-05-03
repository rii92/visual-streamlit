import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_title="Nickel Mining Analysis Dashboard")

# App title and description
st.title("Nickel Mining Analysis Dashboard")
st.markdown("Analysis of nickel mining operations, land changes, and financial implications")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", ["Map Analysis", "Financial Estimation", "Stakeholder Analysis"])

# Sample data - in a real app, you would load actual data
@st.cache_data
def load_sample_data():
    # Sample mining locations
    mining_locations = pd.DataFrame({
        'name': ['Tambang A', 'Tambang B', 'Tambang C', 'Tambang D'],
        'lat': [-2.5489, -3.9778, -1.2456, -2.1123],
        'lon': [120.1989, 122.5632, 117.3421, 119.4567],
        'area_2020': [150, 200, 300, 180],  # hectares
        'area_2023': [320, 450, 520, 310],  # hectares
        'company': ['PT Nikel Utama', 'PT Mining Sejahtera', 'PT Mineral Abadi', 'PT Tambang Makmur']
    })
    
    # Sample financial data
    financial_data = pd.DataFrame({
        'mine': ['Tambang A', 'Tambang B', 'Tambang C', 'Tambang D'],
        'revenue_per_ha': [250000, 300000, 280000, 270000],  # USD per hectare
        'cost_per_ha': [120000, 150000, 130000, 125000],  # USD per hectare
        'tax_paid_2022': [2500000, 3200000, 4100000, 2800000],  # USD
    })
    
    # Sample stakeholder data
    stakeholders = pd.DataFrame({
        'name': ['John Doe', 'Jane Smith', 'Robert Johnson', 'Maria Garcia', 'Ali Wong', 'Budi Santoso'],
        'role': ['CEO', 'Government Official', 'Investor', 'Local Official', 'Board Member', 'Regional Director'],
        'company': ['PT Nikel Utama', 'Ministry of Mining', 'Investment Corp', 'Local Government', 'PT Mining Sejahtera', 'PT Mineral Abadi'],
        'connected_mine': ['Tambang A', 'Multiple', 'Tambang B', 'Tambang C', 'Tambang B', 'Tambang C'],
        'suspicious_transactions': [2, 5, 0, 3, 1, 4]
    })
    
    # Sample transaction data
    np.random.seed(42)
    dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='W')
    transactions = []
    
    for stakeholder in stakeholders['name']:
        for date in dates:
            if np.random.random() > 0.8:  # Only generate some transactions
                amount = np.random.randint(5000, 500000)
                transactions.append({
                    'date': date,
                    'person': stakeholder,
                    'amount': amount,
                    'type': np.random.choice(['Bank Transfer', 'E-Wallet', 'Cash Deposit']),
                    'flag': 'Suspicious' if amount > 300000 else 'Normal'
                })
    
    transactions_df = pd.DataFrame(transactions)
    
    return mining_locations, financial_data, stakeholders, transactions_df

mining_data, financial_data, stakeholders, transactions = load_sample_data()

if page == "Map Analysis":
    st.header("Mining Location Analysis")
    
    # Map showing mining locations with full-width layout
    st.subheader("Nickel Mining Locations")
    
    # Create tabs for different map views
    map_tabs = st.tabs(["Interactive Map", "Heatmap", "Satellite View"])
    
    with map_tabs[0]:
        # Enhanced interactive map with data science color scheme
        m = folium.Map(location=[-3.0, 120.0], zoom_start=6, tiles="CartoDB positron")
        
        # Add tile layer control with data science oriented themes
        folium.TileLayer('CartoDB dark_matter').add_to(m)
        folium.TileLayer('CartoDB positron').add_to(m)
        folium.TileLayer(
            'Stamen Toner',
            attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.'
        ).add_to(m)
        folium.LayerControl().add_to(m)
        
        # Add mining locations with enhanced markers using data science color palette
        for idx, row in mining_data.iterrows():
            area_change = row['area_2023'] - row['area_2020']
            percent_change = (area_change / row['area_2020']) * 100
            
            popup_text = f"""
            <div style="font-family: 'Roboto', sans-serif; width: 250px;">
                <h4 style="color: #2C3E50; margin-bottom: 10px;">{row['name']}</h4>
                <p><b>Company:</b> {row['company']}</p>
                <p><b>Area 2020:</b> {row['area_2020']} ha</p>
                <p><b>Area 2023:</b> {row['area_2023']} ha</p>
                <p><b>Change:</b> +{area_change} ha ({percent_change:.1f}%)</p>
                <p><b>Estimated Revenue:</b> ${row['area_2023'] * financial_data[financial_data['mine'] == row['name']]['revenue_per_ha'].values[0]:,.0f}</p>
            </div>
            """
            
            # Data science color palette based on change intensity
            color = '#3498db' if area_change < 100 else '#f39c12' if area_change < 200 else '#e74c3c'
            
            # Create a circle marker with data science styling
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=area_change/20,  # Size based on change
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fill=True,
                fill_opacity=0.8,
                fill_color=color,
                weight=2
            ).add_to(m)
            
            # Add mine name as a marker with improved styling
            folium.Marker(
                location=[row['lat'], row['lon']],
                icon=folium.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(75, 0),
                    html=f'<div style="font-size: 12pt; font-weight: bold; color: #2c3e50; background-color: rgba(255,255,255,0.8); padding: 4px 8px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">{row["name"]}</div>'
                )
            ).add_to(m)
        
        # Add a modern legend with data science styling
        legend_html = '''
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: rgba(255,255,255,0.9); padding: 12px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
            <h4 style="margin-top: 0; margin-bottom: 10px; color: #2c3e50;">Land Change Impact</h4>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 15px; height: 15px; border-radius: 50%; background-color: #3498db; margin-right: 10px;"></div>
                <span style="color: #2c3e50;">Low Impact (< 100 ha)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 15px; height: 15px; border-radius: 50%; background-color: #f39c12; margin-right: 10px;"></div>
                <span style="color: #2c3e50;">Medium Impact (100-200 ha)</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 15px; height: 15px; border-radius: 50%; background-color: #e74c3c; margin-right: 10px;"></div>
                <span style="color: #2c3e50;">High Impact (> 200 ha)</span>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Display the map with full width
        folium_static(m, width=1400, height=600)
    
    with map_tabs[1]:
        # Alternative to heatmap using circle markers
        heatmap = folium.Map(location=[-3.0, 120.0], zoom_start=6, tiles="CartoDB dark_matter")
        
        # Create a heat-like visualization using circle markers
        for idx, row in mining_data.iterrows():
            weight = (row['area_2023'] - row['area_2020']) / 10
            
            # Color based on weight
            color = '#3498db' if weight < 10 else '#f39c12' if weight < 20 else '#e74c3c'
            
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=weight,  # Size based on weight
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"{row['name']}: Change of {row['area_2023'] - row['area_2020']} ha"
            ).add_to(heatmap)
        
        # Display the map with full width
        folium_static(heatmap, width=1400, height=600)
    
    with map_tabs[2]:
        # Satellite view with data science overlays
        satellite = folium.Map(location=[-3.0, 120.0], zoom_start=6, tiles="CartoDB positron")
        
        # Add satellite imagery
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=False,
            control=True
        ).add_to(satellite)
        
        # Add mining locations with area visualization using data science styling
        for idx, row in mining_data.iterrows():
            area_change = row['area_2023'] - row['area_2020']
            
            # Create a circle to represent the mining area with data science color
            folium.Circle(
                location=[row['lat'], row['lon']],
                radius=area_change * 100,  # Scale for visibility
                popup=row['name'],
                color='#e74c3c',
                fill=True,
                fill_color='#e74c3c',
                fill_opacity=0.5,
                stroke=True,
                weight=2
            ).add_to(satellite)
            
            # Add a label with the mine name
            folium.Marker(
                location=[row['lat'], row['lon']],
                icon=folium.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(75, 0),
                    html=f'<div style="font-size: 12pt; font-weight: bold; color: white; background-color: rgba(44,62,80,0.8); padding: 4px 8px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.3);">{row["name"]}</div>'
                )
            ).add_to(satellite)
        
        # Display the satellite view with full width
        folium_static(satellite, width=1400, height=600)
    
    # Enhanced land change analysis
    st.subheader("Land Change Analysis (2020-2023)")
    
    # Create three columns for better visualization
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart of land area changes with enhanced styling
        mining_data['area_change'] = mining_data['area_2023'] - mining_data['area_2020']
        mining_data['percent_change'] = (mining_data['area_change'] / mining_data['area_2020']) * 100
        
        fig = px.bar(mining_data, x='name', y=['area_2020', 'area_2023'], 
                    barmode='group', 
                    title='Mining Area Comparison (hectares)',
                    labels={'value': 'Area (hectares)', 'name': 'Mining Location', 'variable': 'Year'},
                    color_discrete_map={'area_2020': '#3498db', 'area_2023': '#e74c3c'})
        
        fig.update_layout(
            legend_title_text='Year',
            plot_bgcolor='rgba(240, 240, 240, 0.8)',
            font=dict(family="Arial", size=12),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pie chart of total land usage with enhanced styling
        fig = px.pie(mining_data, values='area_2023', names='name', 
                    title='Current Mining Area Distribution',
                    color_discrete_sequence=px.colors.qualitative.Bold)
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            font=dict(family="Arial", size=12),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Add a new visualization for land change
    st.subheader("Land Change Visualization")
    
    # Create a waterfall chart to show land changes
    change_data = mining_data[['name', 'area_change']].copy()
    change_data = change_data.sort_values('area_change', ascending=False)
    
    fig = px.bar(change_data, x='name', y='area_change',
                title='Land Area Change by Mining Location (2020-2023)',
                labels={'area_change': 'Change in Hectares', 'name': 'Mining Location'},
                color='area_change',
                color_continuous_scale=['green', 'yellow', 'red'])
    
    fig.update_layout(
        plot_bgcolor='rgba(240, 240, 240, 0.8)',
        font=dict(family="Arial", size=12),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Time slider for temporal analysis (enhanced)
    st.subheader("Temporal Land Change Analysis")
    
    year = st.slider("Select Year", 2020, 2023, 2020)
    
    # Simulate data for years in between
    if year == 2020:
        current_areas = mining_data['area_2020'].tolist()
    elif year == 2023:
        current_areas = mining_data['area_2023'].tolist()
    else:
        # Linear interpolation for years in between
        progress = (year - 2020) / 3
        current_areas = [mining_data['area_2020'][i] + progress * mining_data['area_change'][i] 
                        for i in range(len(mining_data))]
    
    temp_df = pd.DataFrame({
        'name': mining_data['name'],
        'area': current_areas
    })
    
    # Create an animated bar chart
    fig = px.bar(temp_df, x='name', y='area', 
                title=f'Mining Area in {year} (hectares)',
                color='area',
                color_continuous_scale=['blue', 'purple', 'red'])
    
    fig.update_layout(
        plot_bgcolor='rgba(240, 240, 240, 0.8)',
        font=dict(family="Arial", size=12),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Add environmental impact metrics
    st.subheader("Environmental Impact Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    total_change = mining_data['area_change'].sum()
    
    with col1:
        st.metric("Total Land Change", f"{total_change} hectares", f"{total_change/3:.1f} ha/year")
    
    with col2:
        # Estimate CO2 impact (simplified calculation)
        co2_per_ha = 300  # tons of CO2 per hectare of forest
        co2_impact = total_change * co2_per_ha
        st.metric("Estimated CO2 Impact", f"{co2_impact:,.0f} tons", f"{co2_impact/3:,.1f} tons/year")
    
    with col3:
        # Estimate biodiversity impact (simplified index)
        biodiversity_index = total_change * 0.05
        st.metric("Biodiversity Impact Index", f"{biodiversity_index:.1f}", "Based on land change")

elif page == "Financial Estimation":
    st.header("Financial Impact Analysis")
    
    # Merge mining and financial data
    analysis_df = pd.merge(mining_data, financial_data, left_on='name', right_on='mine')
    
    # Calculate financial metrics
    analysis_df['land_change'] = analysis_df['area_2023'] - analysis_df['area_2020']
    analysis_df['estimated_revenue'] = analysis_df['land_change'] * analysis_df['revenue_per_ha']
    analysis_df['estimated_cost'] = analysis_df['land_change'] * analysis_df['cost_per_ha']
    analysis_df['estimated_profit'] = analysis_df['estimated_revenue'] - analysis_df['estimated_cost']
    
    # Display financial metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Estimated Revenue", f"${analysis_df['estimated_revenue'].sum():,.0f}")
    
    with col2:
        st.metric("Total Estimated Cost", f"${analysis_df['estimated_cost'].sum():,.0f}")
    
    with col3:
        st.metric("Total Estimated Profit", f"${analysis_df['estimated_profit'].sum():,.0f}")
    
    # Financial breakdown by mine
    st.subheader("Financial Breakdown by Mining Location")
    
    fig = px.bar(analysis_df, x='name', y=['estimated_revenue', 'estimated_cost', 'estimated_profit'], 
                barmode='group', title='Financial Estimation Based on Land Change',
                labels={'value': 'USD', 'name': 'Mining Location', 'variable': 'Financial Metric'})
    st.plotly_chart(fig)
    
    # Profitability analysis
    st.subheader("Profitability Analysis")
    
    analysis_df['profit_per_ha'] = analysis_df['estimated_profit'] / analysis_df['land_change']
    
    fig = px.scatter(analysis_df, x='land_change', y='estimated_profit', size='area_2023', 
                    color='profit_per_ha', hover_name='name',
                    labels={'land_change': 'Land Change (ha)', 'estimated_profit': 'Estimated Profit (USD)'},
                    title='Profit vs Land Change')
    st.plotly_chart(fig)
    
    # Tax analysis
    st.subheader("Tax Contribution Analysis")
    
    fig = px.pie(analysis_df, values='tax_paid_2022', names='name', 
                title='Tax Contribution by Mining Operation (2022)')
    st.plotly_chart(fig)
    
    # Cost-benefit calculator
    st.subheader("Cost-Benefit Calculator")
    
    selected_mine = st.selectbox("Select Mining Operation", mining_data['name'])
    mine_data = analysis_df[analysis_df['name'] == selected_mine].iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        custom_area = st.number_input("Land Area (hectares)", value=float(mine_data['land_change']), step=10.0)
    
    with col2:
        price_factor = st.slider("Price Factor", 0.5, 1.5, 1.0, 0.1)
    
    estimated_revenue = custom_area * mine_data['revenue_per_ha'] * price_factor
    estimated_cost = custom_area * mine_data['cost_per_ha']
    estimated_profit = estimated_revenue - estimated_cost
    
    st.metric("Estimated Revenue", f"${estimated_revenue:,.0f}")
    st.metric("Estimated Cost", f"${estimated_cost:,.0f}")
    st.metric("Estimated Profit", f"${estimated_profit:,.0f}")

elif page == "Stakeholder Analysis":
    st.header("Stakeholder and Financial Transaction Analysis")
    
    # Stakeholder network
    st.subheader("Key Stakeholders in Mining Operations")
    
    # Display stakeholder table
    st.dataframe(stakeholders)
    
    # Suspicious transactions analysis
    st.subheader("Suspicious Transaction Analysis")
    
    suspicious_transactions = transactions[transactions['flag'] == 'Suspicious']
    
    fig = px.histogram(suspicious_transactions, x='person', title='Suspicious Transactions by Person')
    st.plotly_chart(fig)
    
    # Transaction timeline
    st.subheader("Transaction Timeline")
    
    # Group by date and person
    timeline_data = transactions.groupby(['date', 'person'])['amount'].sum().reset_index()
    
    fig = px.line(timeline_data, x='date', y='amount', color='person', 
                title='Transaction Timeline by Person')
    st.plotly_chart(fig)
    
    # Transaction type analysis
    st.subheader("Transaction Type Analysis")
    
    fig = px.pie(transactions, values='amount', names='type', title='Transaction Distribution by Type')
    st.plotly_chart(fig)
    
    # Detailed transaction explorer
    st.subheader("Transaction Explorer")
    
    person_filter = st.multiselect("Filter by Person", options=stakeholders['name'].tolist(), default=[])
    date_range = st.date_input("Select Date Range", 
                              value=(datetime(2022, 1, 1), datetime(2023, 12, 31)),
                              max_value=datetime(2023, 12, 31))
    
    filtered_transactions = transactions
    
    if person_filter:
        filtered_transactions = filtered_transactions[filtered_transactions['person'].isin(person_filter)]
    
    filtered_transactions = filtered_transactions[
        (filtered_transactions['date'] >= pd.Timestamp(date_range[0])) & 
        (filtered_transactions['date'] <= pd.Timestamp(date_range[1]))
    ]
    
    st.dataframe(filtered_transactions.sort_values('date', ascending=False))
    
    # Stakeholder risk assessment
    st.subheader("Stakeholder Risk Assessment")
    
    # Calculate risk score based on suspicious transactions and role
    stakeholder_risk = stakeholders.copy()
    stakeholder_risk['risk_score'] = stakeholder_risk['suspicious_transactions'] * 20
    
    # Add extra risk for government officials
    stakeholder_risk.loc[stakeholder_risk['role'].str.contains('Official'), 'risk_score'] += 30
    
    fig = px.bar(stakeholder_risk.sort_values('risk_score', ascending=False), 
                x='name', y='risk_score', color='role',
                title='Stakeholder Risk Assessment')
    st.plotly_chart(fig)

# Footer
st.markdown("---")
st.markdown("© 2023 Nickel Mining Analysis Dashboard | Data is simulated for demonstration purposes")




