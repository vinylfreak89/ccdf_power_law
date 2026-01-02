import sys
sys.path.append('code/data')
sys.path.append('code/analysis')
from load_data import load_asset
from synthetic_vix import calculate_synthetic_vix
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

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

# Find sharp peaks using scipy
# prominence = how much peak stands out from surroundings
# distance = minimum distance between peaks
mean_dev_clean = df['Mean_Deviation'].dropna()
peaks, properties = find_peaks(mean_dev_clean.values, prominence=0.005, distance=60)

print(f"✓ Found {len(peaks)} sharp peaks")

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), sharex=True)

# Top: SPX price with peak markers
peak_dates = mean_dev_clean.iloc[peaks].index
for peak_idx in peak_dates:
    peak_date = df.iloc[peak_idx]['Date']
    ax1.axvline(x=peak_date, color='red', linewidth=2, alpha=0.7)

ax1.semilogy(df['Date'], df['Close'], color='black', linewidth=1, alpha=0.8)
ax1.set_ylabel('SPX Price (log scale)', fontsize=11, fontweight='bold')
ax1.set_title('SPX Price with Sharp Deviation Peaks (Red lines)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Bottom: Mean deviation with peaks marked
ax2.plot(df['Date'], df['Mean_Deviation'], color='blue', linewidth=1.5, alpha=0.8)
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

# Mark the peaks
for peak_idx in peak_dates:
    peak_date = df.iloc[peak_idx]['Date']
    peak_val = df.iloc[peak_idx]['Mean_Deviation']
    ax2.plot(peak_date, peak_val, 'ro', markersize=8, label='Sharp Peak' if peak_idx == peak_dates[0] else '')

ax2.set_ylabel('Mean CCDF Deviation', fontsize=11, fontweight='bold')
ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('sharp_peaks.png', dpi=300, bbox_inches='tight')
print("✓ Saved sharp_peaks.png")

# Print peak dates
print("\nPeak dates:")
for peak_idx in peak_dates:
    print(f"  {df.iloc[peak_idx]['Date'].strftime('%Y-%m-%d')}: {df.iloc[peak_idx]['Mean_Deviation']:.6f}")

