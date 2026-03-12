import pandas as pd
import streamlit as st

@st.cache_data
def load_country_data():
    try:
        
        df = pd.read_csv("data/countries_cleaned_merged.csv",encoding="latin1")
    except FileNotFoundError:
        df = pd.read_csv("countries_cleaned_merged.csv")
        
    # 1. Standardize column names (lowercase)
    df.columns = df.columns.str.lower()
    
    # 2. RENAME columns to match what the app expects
    # This fixes the "area not in index" error
    rename_map = {
        'land area(km2)': 'area',
        'cpi change (%)': 'cpi_change',
        'fertility rate': 'fertility_rate'
    }
    df = df.rename(columns=rename_map)

    # 3. CLEANING: Force numeric columns
    # Now 'area' exists, so this loop will work
    for col in ['population', 'area']:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '')
                .apply(pd.to_numeric, errors='coerce')
                .fillna(0)
                .astype(int)
            )

    # 4. Ensure Lat/Lon are floats
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    # 5. Safety Checks (Create missing columns if they don't exist)
    if 'region' not in df.columns:
        df['region'] = 'Unknown'
    if 'area' not in df.columns:
        df['area'] = 0  # Fallback to prevent crash
    if 'continent' not in df.columns:
        st.error("CSV is missing 'continent' column!")
    
    return df