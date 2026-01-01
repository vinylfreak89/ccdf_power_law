"""Load VIX data and calculate returns"""
import pandas as pd
import numpy as np

def load_vix():
    """Load VIX data from FRED format"""
    df = pd.read_csv('/mnt/user-data/uploads/VIXCLS.csv')
    df.columns = ['Date', 'Close']  # Rename to standard format
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    
    # VIX doesn't have OHLV, just close
    df['Open'] = df['Close']
    df['High'] = df['Close']
    df['Low'] = df['Close']
    df['Volume'] = 0
    
    # Calculate returns
    df['Return'] = df['Close'].pct_change() * 100
    df = df.dropna(subset=['Return'])
    
    # Remove extreme outliers
    df = df[np.abs(df['Return']) < 100].reset_index(drop=True)
    
    print(f"✓ Loaded VIX: {len(df):,} days from {df['Date'].min().date()} to {df['Date'].max().date()}")
    
    return df
