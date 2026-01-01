"""
Synthetic VIX Calculator

VIX measures 30-day implied volatility. We can approximate it using realized volatility
from historical returns.

Real VIX calculation is complex (uses options), but we can approximate with:
- Rolling standard deviation of returns
- Annualized (multiply by sqrt(252))
- Scaled to match VIX's typical range
"""
import pandas as pd
import numpy as np


def calculate_synthetic_vix(df, window=21, annualize=True):
    """
    Calculate synthetic VIX from returns using rolling realized volatility.
    
    Args:
        df: DataFrame with Return column
        window: Rolling window (default 21 days ≈ 1 month)
        annualize: If True, annualize volatility (multiply by sqrt(252))
        
    Returns:
        DataFrame with SyntheticVIX column
    """
    df = df.copy()
    
    # Calculate rolling standard deviation
    rolling_std = df['Return'].rolling(window=window).std()
    
    if annualize:
        # Annualize: vol * sqrt(252 trading days)
        rolling_std = rolling_std * np.sqrt(252)
    
    df['SyntheticVIX'] = rolling_std
    
    return df


def compare_with_real_vix(spx_df, vix_df, window=21):
    """
    Compare synthetic VIX with real VIX data.
    
    Args:
        spx_df: SPX DataFrame with Return column
        vix_df: VIX DataFrame with Close column
        window: Rolling window for synthetic calculation
        
    Returns:
        Merged DataFrame with both VIX measures
    """
    # Calculate synthetic VIX
    spx_with_synthetic = calculate_synthetic_vix(spx_df, window=window)
    
    # Merge with real VIX
    merged = spx_with_synthetic.merge(
        vix_df[['Date', 'Close']], 
        on='Date', 
        how='inner',
        suffixes=('', '_VIX')
    )
    merged = merged.rename(columns={'Close_VIX': 'RealVIX'})
    
    # Calculate correlation
    correlation = merged[['SyntheticVIX', 'RealVIX']].corr().iloc[0, 1]
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean((merged['SyntheticVIX'] - merged['RealVIX'])**2))
    
    # Calculate mean absolute error
    mae = np.mean(np.abs(merged['SyntheticVIX'] - merged['RealVIX']))
    
    stats = {
        'correlation': correlation,
        'rmse': rmse,
        'mae': mae,
        'n_days': len(merged),
        'date_range': (merged['Date'].min(), merged['Date'].max())
    }
    
    return merged, stats


if __name__ == '__main__':
    import sys
    sys.path.append('/mnt/user-data/outputs/code/data')
    from load_data import load_asset
    
    # Load SPX
    print("Loading SPX data...")
    spx = load_asset('_spx_d.csv', min_date='1990-01-01')
    
    # Load VIX
    print("Loading VIX data...")
    vix = pd.read_csv('/mnt/user-data/uploads/VIXCLS.csv')
    vix.columns = ['Date', 'Close']
    vix['Date'] = pd.to_datetime(vix['Date'])
    
    # Test different window sizes
    print("\nTesting different rolling windows:")
    print(f"{'Window':<10} {'Correlation':<15} {'RMSE':<10} {'MAE':<10}")
    print("-" * 50)
    
    best_corr = 0
    best_window = None
    
    for window in [10, 15, 21, 30, 42, 63]:
        merged, stats = compare_with_real_vix(spx, vix, window=window)
        print(f"{window:<10} {stats['correlation']:<15.3f} {stats['rmse']:<10.2f} {stats['mae']:<10.2f}")
        
        if stats['correlation'] > best_corr:
            best_corr = stats['correlation']
            best_window = window
    
    print(f"\n✓ Best window: {best_window} days (correlation: {best_corr:.3f})")
    
    # Use best window for full analysis
    merged, stats = compare_with_real_vix(spx, vix, window=best_window)
    
    print(f"\n=== VALIDATION STATS (window={best_window}) ===")
    print(f"Correlation: {stats['correlation']:.3f}")
    print(f"RMSE: {stats['rmse']:.2f}")
    print(f"MAE: {stats['mae']:.2f}")
    print(f"Days: {stats['n_days']:,}")
    print(f"Range: {stats['date_range'][0].date()} to {stats['date_range'][1].date()}")
