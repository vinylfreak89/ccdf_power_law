"""
Power Law Fit Quality Analysis

Analyzes how well returns follow a power law distribution and how this changes over time.

Questions to answer:
1. Does the power law fit well in general?
2. Does fit quality vary over time (rolling windows)?
3. Does fit quality vary by volatility regime?
4. WHERE does the fit deviate (by return magnitude)?
5. Does this vary by asset class?
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def calculate_fit_quality(returns, min_return=0.5):
    """
    Calculate power law fit quality metrics.
    
    Args:
        returns: Array of absolute returns
        min_return: Minimum return for tail fitting
        
    Returns:
        dict with:
            - alpha: Power law exponent
            - r_squared: Overall fit quality (0-1)
            - residuals: Array of residuals by magnitude
            - x_vals: Corresponding x values for residuals
    """
    # Sort returns in descending order
    sorted_returns = np.sort(np.abs(returns))[::-1]
    n = len(sorted_returns)
    ccdf = np.arange(1, n+1) / n
    
    # Filter to tail (> min_return)
    valid_mask = (sorted_returns > 0) & (ccdf > 0)
    tail_mask = sorted_returns[valid_mask] > min_return
    
    if tail_mask.sum() < 10:
        return None
    
    x = sorted_returns[valid_mask][tail_mask]
    y = ccdf[valid_mask][tail_mask]
    
    # Fit power law in log-log space
    log_x = np.log(x)
    log_y = np.log(y)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    alpha = -slope
    
    # Calculate R²
    predicted_log_y = slope * log_x + intercept
    ss_res = np.sum((log_y - predicted_log_y) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    # Calculate residuals across full range
    residuals = log_y - predicted_log_y
    
    return {
        'alpha': alpha,
        'r_squared': r_squared,
        'residuals': residuals,
        'x_vals': x,
        'slope': slope,
        'intercept': intercept
    }


def rolling_fit_quality(df, window=60):
    """
    Calculate rolling power law fit quality.
    
    Args:
        df: DataFrame with Return column
        window: Rolling window size in days
        
    Returns:
        DataFrame with added columns:
            - RollingAlpha
            - RollingR2
    """
    df = df.copy()
    df['RollingAlpha'] = np.nan
    df['RollingR2'] = np.nan
    
    for i in range(window, len(df)):
        window_returns = df.iloc[i-window:i]['Return'].values
        fit = calculate_fit_quality(window_returns)
        
        if fit is not None:
            df.loc[i, 'RollingAlpha'] = fit['alpha']
            df.loc[i, 'RollingR2'] = fit['r_squared']
    
    return df


def analyze_fit_by_regime(df, vix_df=None):
    """
    Analyze fit quality by volatility regime.
    
    Args:
        df: DataFrame with Return column
        vix_df: Optional VIX data to define regimes
        
    Returns:
        dict with regime-specific fit quality
    """
    if vix_df is not None:
        # Merge VIX data
        merged = df.merge(vix_df[['Date', 'Close']], on='Date', how='left', suffixes=('', '_VIX'))
        merged = merged.dropna(subset=['Close_VIX'])
        
        # Define regimes by VIX level
        vix_20 = merged['Close_VIX'].quantile(0.33)
        vix_80 = merged['Close_VIX'].quantile(0.67)
        
        low_vol = merged[merged['Close_VIX'] <= vix_20]['Return'].values
        med_vol = merged[(merged['Close_VIX'] > vix_20) & (merged['Close_VIX'] <= vix_80)]['Return'].values
        high_vol = merged[merged['Close_VIX'] > vix_80]['Return'].values
        
        return {
            'low_vol': calculate_fit_quality(low_vol),
            'med_vol': calculate_fit_quality(med_vol),
            'high_vol': calculate_fit_quality(high_vol),
            'vix_thresholds': (vix_20, vix_80)
        }
    else:
        # Use realized volatility to define regimes
        df = df.copy()
        df['RealizedVol'] = df['Return'].rolling(30).std()
        
        vol_33 = df['RealizedVol'].quantile(0.33)
        vol_67 = df['RealizedVol'].quantile(0.67)
        
        low_vol = df[df['RealizedVol'] <= vol_33]['Return'].values
        med_vol = df[(df['RealizedVol'] > vol_33) & (df['RealizedVol'] <= vol_67)]['Return'].values
        high_vol = df[df['RealizedVol'] > vol_67]['Return'].values
        
        return {
            'low_vol': calculate_fit_quality(low_vol),
            'med_vol': calculate_fit_quality(med_vol),
            'high_vol': calculate_fit_quality(high_vol),
            'vol_thresholds': (vol_33, vol_67)
        }


def analyze_residuals_by_magnitude(returns, n_bins=20):
    """
    Analyze where the power law fit deviates by return magnitude.
    
    Returns:
        dict with bins and average residuals
    """
    fit = calculate_fit_quality(returns)
    if fit is None:
        return None
    
    # Bin residuals by magnitude
    x_vals = fit['x_vals']
    residuals = fit['residuals']
    
    # Create log-spaced bins
    bins = np.logspace(np.log10(x_vals.min()), np.log10(x_vals.max()), n_bins)
    bin_indices = np.digitize(x_vals, bins)
    
    bin_centers = []
    bin_residuals = []
    
    for i in range(1, len(bins)):
        mask = bin_indices == i
        if mask.sum() > 0:
            bin_centers.append(np.exp(np.mean(np.log(x_vals[mask]))))
            bin_residuals.append(np.mean(residuals[mask]))
    
    return {
        'bin_centers': np.array(bin_centers),
        'bin_residuals': np.array(bin_residuals)
    }


if __name__ == '__main__':
    import sys
    sys.path.append('/mnt/user-data/outputs/code/data')
    from load_data import load_asset
    
    # Test on SPX
    print("Testing power law fit quality analysis on SPX...")
    df = load_asset('_spx_d.csv', min_date='1920-01-01')
    
    # Overall fit
    fit = calculate_fit_quality(df['Return'].values)
    print(f"\nOverall SPX fit:")
    print(f"  Alpha: {fit['alpha']:.3f}")
    print(f"  R²: {fit['r_squared']:.3f}")
    
    # Rolling fit
    print("\nCalculating rolling fit quality...")
    df_rolling = rolling_fit_quality(df, window=252)
    print(f"  Mean rolling R²: {df_rolling['RollingR2'].mean():.3f}")
    print(f"  Std rolling R²: {df_rolling['RollingR2'].std():.3f}")
    
    # By regime
    print("\nFit quality by realized vol regime:")
    regime_fits = analyze_fit_by_regime(df)
    for regime in ['low_vol', 'med_vol', 'high_vol']:
        fit = regime_fits[regime]
        if fit:
            print(f"  {regime}: Alpha={fit['alpha']:.3f}, R²={fit['r_squared']:.3f}")
    
    print("\n✓ Analysis complete!")
