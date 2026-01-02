import sys
sys.path.append('code/data')
sys.path.append('code/analysis')
from load_data import load_asset
from synthetic_vix import calculate_synthetic_vix
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calculate_alpha(returns, min_return=0.5, min_points=5):
    """Calculate power law alpha from returns"""
    sorted_returns = np.sort(np.abs(returns))[::-1]
    n = len(sorted_returns)
    ccdf = np.arange(1, n+1) / n
    valid_mask = (sorted_returns > 0) & (ccdf > 0)
    tail_mask = sorted_returns[valid_mask] > min_return
    if tail_mask.sum() < min_points:
        return None, None, None, None
    x = sorted_returns[valid_mask][tail_mask]
    y = ccdf[valid_mask][tail_mask]
    log_x = np.log(x)
    log_y = np.log(y)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    alpha = -slope
    return x, y, alpha, intercept

def calculate_mean_deviation(df, window=60):
    """Calculate mean CCDF deviation"""
    mean_deviations = []
    for i in range(len(df)):
        if i < window:
            mean_deviations.append(np.nan)
        else:
            returns = df.iloc[i-window:i]['Return'].values
            x, y, alpha, intercept = calculate_alpha(returns)
            
            if alpha is not None:
                power_law_fit = np.exp(intercept) * (x ** (-alpha))
                deviation = y - power_law_fit
                mask = (x >= 0.5) & (x <= 3.0)
                if mask.sum() > 0:
                    mean_dev = np.mean(deviation[mask])
                    mean_deviations.append(mean_dev)
                else:
                    mean_deviations.append(np.nan)
            else:
                mean_deviations.append(np.nan)
    return mean_deviations

# Assets to test (one from each category)
assets = [
    ('_ndx_d.csv', 'NASDAQ (NDX)'),
    ('nvda_us_d.csv', 'NVIDIA'),
    ('btc_v_d.csv', 'Bitcoin'),
    ('xauusd_d.csv', 'Gold'),
    ('tlt_us_d.csv', 'Bonds (TLT)')
]

fig, axes = plt.subplots(len(assets), 2, figsize=(20, 4*len(assets)))

for idx, (filename, name) in enumerate(assets):
    print(f"\nProcessing {name}...")
    df = load_asset(filename)
    df['Mean_Deviation'] = calculate_mean_deviation(df)
    
    pct_above = (df['Mean_Deviation'] > 0).sum() / df['Mean_Deviation'].notna().sum() * 100
    print(f"  % Above zero: {pct_above:.1f}%")
    
    # Left: Price
    axes[idx, 0].semilogy(df['Date'], df['Close'], color='black', linewidth=1, alpha=0.8)
    axes[idx, 0].set_ylabel('Price (log)', fontsize=10, fontweight='bold')
    axes[idx, 0].set_title(f'{name} Price', fontsize=11, fontweight='bold')
    axes[idx, 0].grid(True, alpha=0.3)
    
    # Right: Deviation
    axes[idx, 1].plot(df['Date'], df['Mean_Deviation'], color='blue', linewidth=1.5, alpha=0.8)
    axes[idx, 1].axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.7)
    axes[idx, 1].fill_between(df['Date'], 0, df['Mean_Deviation'], where=(df['Mean_Deviation']>0), 
                      color='green', alpha=0.2)
    axes[idx, 1].fill_between(df['Date'], 0, df['Mean_Deviation'], where=(df['Mean_Deviation']<0), 
                      color='red', alpha=0.2)
    axes[idx, 1].set_ylabel('Mean CCDF Deviation', fontsize=10, fontweight='bold')
    axes[idx, 1].set_title(f'{name} Deviation (Above={pct_above:.1f}%)', fontsize=11, fontweight='bold')
    axes[idx, 1].grid(True, alpha=0.3)

axes[-1, 0].set_xlabel('Date', fontsize=11, fontweight='bold')
axes[-1, 1].set_xlabel('Date', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('multi_asset_deviation.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved multi_asset_deviation.png")

