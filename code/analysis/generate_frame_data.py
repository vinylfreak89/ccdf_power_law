import sys
sys.path.append('code/data')
sys.path.append('code/analysis')
from load_data import load_asset
from synthetic_vix import calculate_synthetic_vix
import numpy as np
import pickle

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

# Calculate rolling alpha and CCDF - sample every 20 days to keep it reasonable
window = 60
print(f"Calculating {window}-day rolling CCDFs...")

frames_data = []
for i in range(window, len(df), 20):  # Every 20 days instead of 5
    returns = df.iloc[i-window:i]['Return'].values
    x, y, alpha, intercept = calculate_alpha(returns)
    
    if alpha is not None:
        # Calculate power law fit at same x points
        power_law_fit = np.exp(intercept) * (x ** (-alpha))
        
        # Calculate deviation
        deviation = y - power_law_fit
        
        frames_data.append({
            'date': df.iloc[i]['Date'],
            'x': x,
            'actual_ccdf': y,
            'power_law': power_law_fit,
            'deviation': deviation,
            'alpha': alpha,
            'vix': df.iloc[i]['SyntheticVIX'],
            'price': df.iloc[i]['Close']
        })

print(f"Generated {len(frames_data)} frames")

# Save frame data
with open('animation_frames/frame_data.pkl', 'wb') as f:
    pickle.dump(frames_data, f)

print("✓ Saved frame data")
