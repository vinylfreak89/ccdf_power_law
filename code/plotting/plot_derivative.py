"""
Plot CCDF derivative by state.

Visualizes the output from calculate_derivative.py (which uses np.diff).
Plots as lines to show where the distribution "bends" from pure power law.
"""
import matplotlib.pyplot as plt
import numpy as np


def plot_derivative(deriv_data, ccdf_data, output_path=None, 
                   asset_name='Asset', date_range=None,
                   xlim=(0.3, 5), ylim=(None, 0)):
    """
    Plot derivatives on two separate panels for clarity.
    Top: State derivatives (GREEN/ORANGE/RED)
    Bottom: All data derivative (baseline)
    
    Args:
        deriv_data: dict from calculate_derivative() with (x_mid, derivative) tuples
        ccdf_data: dict from calculate_ccdf() (not used, kept for API compatibility)
        output_path: If provided, save to this path
        asset_name: Name of asset for title
        date_range: Tuple of (start_date, end_date) for title
        xlim: X-axis limits for both panels
        ylim: Y-axis limits for derivative panels (default: show all data below 0)
        
    Returns:
        fig, (ax1, ax2) objects
    """
    # Create 2-panel plot
    fig, axes = plt.subplots(2, 1, figsize=(20, 16))
    plt.subplots_adjust(left=0.08, right=0.95, top=0.94, bottom=0.06, hspace=0.3)
    
    # Top panel: STATE DERIVATIVES (GREEN/ORANGE/RED)
    ax1 = axes[0]
    ax1.axvspan(0.5, 3.0, alpha=0.15, color='blue', zorder=1)
    
    if 'green' in deriv_data:
        x_mid, derivative = deriv_data['green']
        if len(x_mid) > 0:
            ax1.plot(x_mid, derivative, color='green', alpha=0.7,
                    linewidth=2, label='GREEN')
    
    if 'orange' in deriv_data:
        x_mid, derivative = deriv_data['orange']
        if len(x_mid) > 0:
            ax1.plot(x_mid, derivative, color='orange', alpha=0.9,
                    linewidth=3, label='ORANGE')
    
    if 'red' in deriv_data:
        x_mid, derivative = deriv_data['red']
        if len(x_mid) > 0:
            ax1.plot(x_mid, derivative, color='red', alpha=0.7,
                    linewidth=2, label='RED')
    
    ax1.axhline(0, color='black', linestyle='--', alpha=0.3)
    ax1.set_xlabel('Absolute Return Size (%)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('d(log CCDF)/d(log x)', fontsize=14, fontweight='bold')
    ax1.set_title('State Derivatives (GREEN/ORANGE/RED)', fontsize=16, fontweight='bold')
    ax1.set_xscale('log')
    ax1.set_xlim(xlim)
    ax1.set_ylim(ylim)
    ax1.legend(fontsize=12, loc='lower left')
    ax1.grid(True, alpha=0.3)
    
    # Bottom panel: ALL DATA DERIVATIVE (baseline)
    ax2 = axes[1]
    ax2.axvspan(0.5, 3.0, alpha=0.15, color='blue', zorder=1)
    
    if 'all' in deriv_data:
        x_mid, derivative = deriv_data['all']
        if len(x_mid) > 0:
            ax2.plot(x_mid, derivative, color='black', alpha=0.6, 
                    linewidth=2, label='All Returns (baseline)')
    
    ax2.axhline(0, color='black', linestyle='--', alpha=0.3)
    ax2.set_xlabel('Absolute Return Size (%)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('d(log CCDF)/d(log x)', fontsize=14, fontweight='bold')
    
    # Generate title for bottom panel
    if date_range:
        title = f'{asset_name} All Data Derivative - Baseline ({date_range[0].year}-{date_range[1].year})'
    else:
        title = f'{asset_name} All Data Derivative - Baseline'
    
    ax2.set_title(title, fontsize=16, fontweight='bold')
    ax2.set_xscale('log')
    ax2.set_xlim(xlim)
    ax2.set_ylim(ylim)
    ax2.legend(fontsize=12, loc='lower left')
    ax2.grid(True, alpha=0.3)
    
    if output_path:
        plt.savefig(output_path, dpi=300)
        print(f"✓ Derivative plot saved to {output_path}")
    
    return fig, (ax1, ax2)


if __name__ == '__main__':
    print("Module loaded successfully.")
    print("Usage:")
    print("  from calculate_ccdf import calculate_ccdf")
    print("  from calculate_derivative import calculate_derivative")
    print("  ccdf_data = calculate_ccdf(df)")
    print("  deriv_data = calculate_derivative(ccdf_data)")
    print("  plot_derivative(deriv_data, ccdf_data, output_path='derivative.png')")
