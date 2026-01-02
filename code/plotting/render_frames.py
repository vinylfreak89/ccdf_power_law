import pickle
import matplotlib.pyplot as plt
import sys

# Load frame data
with open('animation_frames/frame_data.pkl', 'rb') as f:
    frames_data = pickle.load(f)

# Get chunk info from command line
start_idx = int(sys.argv[1])
end_idx = int(sys.argv[2])

print(f"Rendering frames {start_idx} to {end_idx}...")

for frame_idx in range(start_idx, end_idx):
    if frame_idx >= len(frames_data):
        break
        
    data = frames_data[frame_idx]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
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
        ax1.set_facecolor('#ffcccc')
    elif data['vix'] < 15:
        ax1.set_facecolor('#ccffcc')
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
    plt.savefig(f'animation_frames/frame_{frame_idx:04d}.png', dpi=100)
    plt.close()

print(f"✓ Rendered {end_idx - start_idx} frames")
