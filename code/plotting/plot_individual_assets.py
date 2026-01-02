import sys
sys.path.append('code/data')
sys.path.append('code/analysis')
from load_data import load_asset
import numpy as np
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

# Assets to test
assets = [
    ('_ndx_d.csv', 'NDX'),
    ('nvda_us_d.csv', 'NVDA'),
    ('btc_v_d.csv', 'BTC'),
    ('xauusd_d.csv', 'GOLD'),
    ('tlt_us_d.csv', 'TLT')
]

for filename, name in assets:
    print(f"\nProcessing {name}...")
    df = load_asset(filename)
    df['Mean_Deviation'] = calculate_mean_deviation(df)
    
    pct_above = (df['Mean_Deviation'] > 0).sum() / df['Mean_Deviation'].notna().sum() * 100
    print(f"  % Above zero: {pct_above:.1f}%")
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), sharex=True)
    
    # Top: Price
    ax1.semilogy(df['Date'], df['Close'], color='black', linewidth=1, alpha=0.8)
    ax1.set_ylabel('Price (log scale)', fontsize=11, fontweight='bold')
    ax1.set_title(f'{name} Price', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Bottom: Deviation
    ax2.plot(df['Date'], df['Mean_Deviation'], color='blue', linewidth=1.5, alpha=0.8)
    ax2.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Zero (CCDF = Power Law)')
    ax2.fill_between(df['Date'], 0, df['Mean_Deviation'], where=(df['Mean_Deviation']>0), 
                      color='green', alpha=0.2, label='Above power law')
    ax2.fill_between(df['Date'], 0, df['Mean_Deviation'], where=(df['Mean_Deviation']<0), 
                      color='red', alpha=0.2, label='Below power law')
    ax2.set_ylabel('Mean CCDF Deviation (0.5-3%)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax2.set_title(f'{name} Deviation - {pct_above:.1f}% above zero', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'deviation_{name.lower()}.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved deviation_{name.lower()}.png")

