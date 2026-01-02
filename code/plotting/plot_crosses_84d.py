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

# Load SPX
print("Loading SPX data...")
df = load_asset('_spx_d.csv', min_date='1990-01-01')
df = calculate_synthetic_vix(df, window=21)

# Calculate rolling mean deviation
window = 60
print(f"Calculating {window}-day rolling mean CCDF deviation...")

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

df['Mean_Deviation'] = mean_deviations

# Calculate baseline - 84 days
baseline_window = 84
df['Baseline'] = df['Mean_Deviation'].rolling(window=baseline_window).mean()

print(f"Mean_Deviation NaN count: {df['Mean_Deviation'].isna().sum()}")
print(f"Baseline NaN count: {df['Baseline'].isna().sum()}")

# Find crosses back under baseline
crosses_under = []
for i in range(1, len(df)):
    if pd.notna(df.iloc[i-1]['Mean_Deviation']) and pd.notna(df.iloc[i]['Mean_Deviation']) and \
       pd.notna(df.iloc[i-1]['Baseline']) and pd.notna(df.iloc[i]['Baseline']):
        if df.iloc[i-1]['Mean_Deviation'] > df.iloc[i-1]['Baseline'] and \
           df.iloc[i]['Mean_Deviation'] <= df.iloc[i]['Baseline']:
            crosses_under.append(i)

print(f"✓ Found {len(crosses_under)} crosses back under baseline")

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), sharex=True)

# Top: SPX price with cross-under markers
for idx in crosses_under:
    ax1.axvline(x=df.iloc[idx]['Date'], color='red', linewidth=1.5, alpha=0.6)

ax1.semilogy(df['Date'], df['Close'], color='black', linewidth=1, alpha=0.8)
ax1.set_ylabel('SPX Price (log scale)', fontsize=11, fontweight='bold')
ax1.set_title(f'SPX with Deviation Crosses Under {baseline_window}d Baseline (Red lines)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Bottom: Mean deviation vs baseline
ax2.plot(df['Date'], df['Mean_Deviation'], color='blue', linewidth=1.5, alpha=0.8, label='Mean Deviation')
ax2.plot(df['Date'], df['Baseline'], color='orange', linewidth=2, alpha=0.8, label=f'{baseline_window}d Baseline')
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

for idx in crosses_under:
    ax2.plot(df.iloc[idx]['Date'], df.iloc[idx]['Mean_Deviation'], 'ro', markersize=6)

ax2.set_ylabel('Mean CCDF Deviation', fontsize=11, fontweight='bold')
ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('deviation_crosses_84d.png', dpi=300, bbox_inches='tight')
print("✓ Saved deviation_crosses_84d.png")

