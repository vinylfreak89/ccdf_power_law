import sys
sys.path.append('code/data')
sys.path.append('code/analysis')
from load_data import load_asset
from synthetic_vix import calculate_synthetic_vix
import numpy as np
import matplotlib.pyplot as plt

def calculate_alpha(returns, min_return=0.5):
    """Calculate power law alpha from returns"""
    sorted_returns = np.sort(np.abs(returns))[::-1]
    n = len(sorted_returns)
    ccdf = np.arange(1, n+1) / n
    valid_mask = (sorted_returns > 0) & (ccdf > 0)
    tail_mask = sorted_returns[valid_mask] > min_return
    if tail_mask.sum() < 10:
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

df['Mean_Deviation'] = np.nan

for i in range(window, len(df)):
    returns = df.iloc[i-window:i]['Return'].values
    x, y, alpha, intercept = calculate_alpha(returns)
    
    if alpha is not None:
        power_law_fit = np.exp(intercept) * (x ** (-alpha))
        deviation = y - power_law_fit
        mask = (x >= 0.5) & (x <= 3.0)
        if mask.sum() > 0:
            mean_dev = np.mean(deviation[mask])
            df.iloc[i, df.columns.get_loc('Mean_Deviation')] = mean_dev

# Calculate slow moving average (1 year = 252 days)
baseline_window = 252
df['Baseline'] = df['Mean_Deviation'].rolling(window=baseline_window).mean()

# Mark peaks (current > baseline)
df['Above_Baseline'] = df['Mean_Deviation'] > df['Baseline']

print("✓ Calculated baseline and peaks")

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), sharex=True)

# Top: SPX price with peak periods shaded
peak_regions = []
in_peak = False
start_idx = None

for i in range(len(df)):
    if df.iloc[i]['Above_Baseline'] and not in_peak:
        in_peak = True
        start_idx = i
    elif not df.iloc[i]['Above_Baseline'] and in_peak:
        in_peak = False
        if start_idx is not None:
            peak_regions.append((start_idx, i-1))
        start_idx = None

if in_peak and start_idx is not None:
    peak_regions.append((start_idx, len(df)-1))

for start, end in peak_regions:
    ax1.axvspan(df.iloc[start]['Date'], df.iloc[end]['Date'], color='red', alpha=0.15)

ax1.semilogy(df['Date'], df['Close'], color='black', linewidth=1, alpha=0.8)
ax1.set_ylabel('SPX Price (log scale)', fontsize=11, fontweight='bold')
ax1.set_title('SPX Price with Deviation Peaks (Red = Above Baseline)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Bottom: Mean deviation vs baseline
for start, end in peak_regions:
    ax2.axvspan(df.iloc[start]['Date'], df.iloc[end]['Date'], color='red', alpha=0.15)

ax2.plot(df['Date'], df['Mean_Deviation'], color='blue', linewidth=1.5, alpha=0.8, label='Mean Deviation')
ax2.plot(df['Date'], df['Baseline'], color='orange', linewidth=2, alpha=0.8, label=f'{baseline_window}d Baseline')
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax2.set_ylabel('Mean CCDF Deviation', fontsize=11, fontweight='bold')
ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('deviation_peaks.png', dpi=300, bbox_inches='tight')
print("✓ Saved deviation_peaks.png")

print(f"\nFound {len(peak_regions)} peak regions")

