import sys
sys.path.append('code/data')
sys.path.append('code/analysis')
from load_data import load_asset
from synthetic_vix import calculate_synthetic_vix
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

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
df = load_asset('_spx_d.csv', min_date='1990-01-01')  # Start from 1990 for cleaner data
df = calculate_synthetic_vix(df, window=21)

# Calculate rolling alpha and CCDF for animation frames
window = 60
print(f"Calculating {window}-day rolling CCDFs...")

frames_data = []
for i in range(window, len(df), 5):  # Every 5 days to keep it manageable
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

# Create animation
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

def animate(frame_idx):
    ax1.clear()
    ax2.clear()
    
    data = frames_data[frame_idx]
    
    # Left panel: Deviation curve
    ax1.plot(data['x'], data['deviation'], 'b-', linewidth=2, alpha=0.8)
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_xlabel('Return Magnitude (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Deviation from Power Law', fontsize=11, fontweight='bold')
    ax1.set_title(f"CCDF Deviation from Power Law\nDate: {data['date'].strftime('%Y-%m-%d')} | α={data['alpha']:.3f} | VIX={data['vix']:.1f}%", 
                  fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0.5, max(data['x']))
    
    # Color code by volatility
    if data['vix'] > 30:
        ax1.set_facecolor('#ffcccc')  # Light red for high vol
    elif data['vix'] < 15:
        ax1.set_facecolor('#ccffcc')  # Light green for low vol
    else:
        ax1.set_facecolor('white')
    
    # Right panel: Actual vs Power Law
    ax2.plot(data['x'], data['actual_ccdf'], 'b-', linewidth=2, label='Actual CCDF', alpha=0.8)
    ax2.plot(data['x'], data['power_law'], 'k--', linewidth=2, label='Power Law Fit', alpha=0.6)
    ax2.set_xlabel('Return Magnitude (%)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('P(|Return| ≥ x)', fontsize=11, fontweight='bold')
    ax2.set_title(f'SPX Price: ${data["price"]:.0f}', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0.5, max(data['x']))
    ax2.set_yscale('log')
    
    plt.tight_layout()

# Create animation
print("Creating animation...")
anim = animation.FuncAnimation(fig, animate, frames=len(frames_data), interval=50, repeat=True)

# Save as mp4
print("Saving animation (this may take a minute)...")
anim.save('ccdf_deviation_animation.mp4', writer='ffmpeg', fps=20, dpi=150)
print("✓ Saved ccdf_deviation_animation.mp4")

