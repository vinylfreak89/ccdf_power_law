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
        # Calculate power law fit
        power_law_fit = np.exp(intercept) * (x ** (-alpha))
        
        # Calculate deviation
        deviation = y - power_law_fit
        
        # Clamp to 0.5% - 3% range
        mask = (x >= 0.5) & (x <= 3.0)
        if mask.sum() > 0:
            mean_dev = np.mean(deviation[mask])
            df.iloc[i, df.columns.get_loc('Mean_Deviation')] = mean_dev

print("✓ Calculated mean deviation")

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), sharex=True)

# Top: SPX price
ax1.semilogy(df['Date'], df['Close'], color='black', linewidth=1, alpha=0.8)
ax1.set_ylabel('SPX Price (log scale)', fontsize=11, fontweight='bold')
ax1.set_title('SPX Price and Mean CCDF Deviation (0.5%-3% returns)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Bottom: Mean deviation
ax2.plot(df['Date'], df['Mean_Deviation'], color='blue', linewidth=1.5, alpha=0.8)
ax2.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Zero line (CCDF = Power Law)')
ax2.fill_between(df['Date'], 0, df['Mean_Deviation'], where=(df['Mean_Deviation']>0), 
                  color='green', alpha=0.2, label='Above power law (fatter tails)')
ax2.fill_between(df['Date'], 0, df['Mean_Deviation'], where=(df['Mean_Deviation']<0), 
                  color='red', alpha=0.2, label='Below power law (thinner tails)')
ax2.set_ylabel('Mean CCDF Deviation', fontsize=11, fontweight='bold')
ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('mean_ccdf_deviation.png', dpi=300, bbox_inches='tight')
print("✓ Saved mean_ccdf_deviation.png")

# Print some stats
print(f"\nMean Deviation Stats:")
print(f"Mean: {df['Mean_Deviation'].mean():.6f}")
print(f"Std: {df['Mean_Deviation'].std():.6f}")
print(f"% Negative (below power law): {(df['Mean_Deviation'] < 0).sum() / df['Mean_Deviation'].notna().sum() * 100:.1f}%")

