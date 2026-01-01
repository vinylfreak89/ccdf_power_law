"""
Load asset data with returns calculated.
"""
import pandas as pd
import numpy as np
import os

def load_asset(filename, min_date=None):
    """
    Load asset data and calculate returns.
    Automatically applies standard date filters based on asset (unless overridden).
    
    Args:
        filename: CSV filename in /mnt/user-data/uploads/
        min_date: Optional minimum date string (e.g., '1920-01-01') to override default filtering.
                  Set to None (default) for automatic filtering, or False for no filtering.
        
    Returns:
        DataFrame with columns: Date, Open, High, Low, Close, Volume, Return
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
    """
    filepath = f'/mnt/user-data/uploads/{filename}'
    
    # Check if file exists
    if not os.path.exists(filepath):
        available_files = [f for f in os.listdir('/mnt/user-data/uploads/') if f.endswith('.csv')]
        error_msg = f"""
ERROR: File not found: {filename}
Path tried: {filepath}

Available CSV files in /mnt/user-data/uploads/:
{chr(10).join(f'  - {f}' for f in available_files)}

ACTION REQUIRED: User needs to upload {filename} to /mnt/user-data/uploads/
"""
        print(error_msg)
        raise FileNotFoundError(error_msg)
    
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    df['Return'] = df['Close'].pct_change() * 100
    df = df.dropna(subset=['Return'])
    
    # Remove extreme outliers (>100% daily moves)
    df = df[np.abs(df['Return']) < 100].reset_index(drop=True)
    
    # Apply date filter
    if min_date is False:
        # No date filtering - use all data
        pass
    elif min_date is not None:
        # User-specified minimum date
        df = df[df['Date'] >= min_date].copy().reset_index(drop=True)
    else:
        # Automatic date filters based on asset
        name = filename.replace('_d.csv', '').replace('_us', '').replace('_v', '').upper()
        
        if name == '_SPX':
            df = df[df['Date'] >= '1920-01-01'].copy().reset_index(drop=True)
        elif name == 'ETH':
            df = df[df['Date'] >= '2016-01-01'].copy().reset_index(drop=True)
        elif name in ['XAUUSD', 'XAGUSD']:
            df = df[df['Date'] >= '1975-01-01'].copy().reset_index(drop=True)
        # All other assets use full date range
    
    print(f"✓ Loaded {filename}: {len(df):,} days from {df['Date'].min().date()} to {df['Date'].max().date()}")
    
    return df


if __name__ == '__main__':
    # Test it
    print("Testing SPX:")
    df_spx = load_asset('_spx_d.csv')
    print(f"  Days: {len(df_spx):,}")
    
    print("\nTesting ETH:")
    df_eth = load_asset('eth_v_d.csv')
    print(f"  Days: {len(df_eth):,}")
    
    print("\nTesting Gold:")
    df_gold = load_asset('xauusd_d.csv')
    print(f"  Days: {len(df_gold):,}")
