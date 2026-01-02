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
df = load_asset('_spx_d.csv')
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

# Calculate baseline
baseline_window = 84
df['Baseline'] = df['Mean_Deviation'].rolling(window=baseline_window).mean()

# Calculate standard deviation of (deviation - baseline)
df['Deviation_From_Baseline'] = df['Mean_Deviation'] - df['Baseline']
rolling_std = df['Deviation_From_Baseline'].rolling(window=252).std()

print(f"Mean_Deviation NaN count: {df['Mean_Deviation'].isna().sum()}")

# Find crosses with BOTH conditions
crosses_under_filtered = []
above_baseline = False
peak_height = 0
cross_up_magnitude = 0

for i in range(1, len(df)):
    if pd.notna(df.iloc[i-1]['Mean_Deviation']) and pd.notna(df.iloc[i]['Mean_Deviation']) and \
       pd.notna(df.iloc[i-1]['Baseline']) and pd.notna(df.iloc[i]['Baseline']):
        
        curr_dev = df.iloc[i]['Mean_Deviation']
        curr_base = df.iloc[i]['Baseline']
        prev_dev = df.iloc[i-1]['Mean_Deviation']
        prev_base = df.iloc[i-1]['Baseline']
        
        # Crossing above baseline - capture the jump magnitude
        if prev_dev <= prev_base and curr_dev > curr_base:
            above_baseline = True
            cross_up_magnitude = curr_dev - prev_dev  # How big was the jump?
            peak_height = curr_dev - curr_base
        
        # While above baseline, track max peak height
        elif above_baseline and curr_dev > curr_base:
            peak_height = max(peak_height, curr_dev - curr_base)
        
        # Crossing back under baseline
        elif above_baseline and prev_dev > prev_base and curr_dev <= curr_base:
            above_baseline = False
            # Only count if BOTH:
            # 1. Peak was > 1σ
            # 2. Initial jump up was > 1σ
            if pd.notna(rolling_std.iloc[i]):
                threshold = rolling_std.iloc[i]
                if peak_height > threshold and abs(cross_up_magnitude) > threshold:
                    crosses_under_filtered.append(i)
            peak_height = 0
            cross_up_magnitude = 0

print(f"✓ Found {len(crosses_under_filtered)} significant crosses (both moves >1σ)")

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), sharex=True)

# Top: SPX price with filtered cross-under markers
for idx in crosses_under_filtered:
    ax1.axvline(x=df.iloc[idx]['Date'], color='red', linewidth=2, alpha=0.8)

ax1.semilogy(df['Date'], df['Close'], color='black', linewidth=1, alpha=0.8)
ax1.set_ylabel('SPX Price (log scale)', fontsize=11, fontweight='bold')
ax1.set_title(f'SPX with Significant Crosses (Peak >1σ AND Jump >1σ)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Bottom: Mean deviation vs baseline
ax2.plot(df['Date'], df['Mean_Deviation'], color='blue', linewidth=1.5, alpha=0.8, label='Mean Deviation')
ax2.plot(df['Date'], df['Baseline'], color='orange', linewidth=2, alpha=0.8, label=f'{baseline_window}d Baseline')
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

for idx in crosses_under_filtered:
    ax2.plot(df.iloc[idx]['Date'], df.iloc[idx]['Mean_Deviation'], 'ro', markersize=8)

ax2.set_ylabel('Mean CCDF Deviation', fontsize=11, fontweight='bold')
ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('deviation_crosses_double_sigma.png', dpi=300, bbox_inches='tight')
print("✓ Saved deviation_crosses_double_sigma.png")

# Print all cross dates
print("\nAll significant cross dates:")
for idx in crosses_under_filtered:
    print(f"  {df.iloc[idx]['Date'].strftime('%Y-%m-%d')}")

