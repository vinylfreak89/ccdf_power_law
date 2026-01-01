"""
Plot CCDF derivative (local power law exponent) by state.

Uses np.gradient() to calculate derivative d(log(CCDF))/d(log(x)).
Plots as lines to show the "bendy bendy" behavior.
"""
import matplotlib.pyplot as plt
import numpy as np


def plot_derivative(ccdf_data, output_path=None, asset_name='Asset', date_range=None,
                   xlim=(0.3, 5), ylim=(-0.25, None)):
    """
    Plot CCDF and its derivative showing where distribution bends.
    Uses np.gradient() and plots as lines (not scatter).
    
    Args:
        ccdf_data: dict from calculate_ccdf() with (x, y) tuples
        output_path: If provided, save to this path
        asset_name: Name of asset for title
        date_range: Tuple of (start_date, end_date) for title
        xlim: X-axis limits for both panels
        ylim: Y-axis limits for derivative panel (default: cut below -0.25)
        
    Returns:
        fig, (ax1, ax2) objects
    """
    # Calculate derivatives using np.gradient
    def get_derivative(x_vals, y_vals):
        """Calculate derivative using gradient (matches original code)"""
        log_x = np.log(x_vals)
        log_y = np.log(y_vals)
        derivative = np.gradient(log_y, log_x)
        return derivative
    
    derivatives = {}
    for state, (x, y) in ccdf_data.items():
        if len(x) > 0:
            derivatives[state] = get_derivative(x, y)
    
    # Create 2-panel plot
    fig, axes = plt.subplots(2, 1, figsize=(20, 16))
    plt.subplots_adjust(left=0.08, right=0.95, top=0.94, bottom=0.06, hspace=0.3)
    
    # Top panel: CCDF
    ax1 = axes[0]
    ax1.axvspan(0.5, 3.0, alpha=0.15, color='blue', zorder=1)
    
    if 'all' in ccdf_data:
        x, y = ccdf_data['all']
        ax1.scatter(x, y, color='black', alpha=0.3, s=20,
                   label='All Returns (full CCDF)', edgecolors='none', zorder=2)
    
    total_days = sum(len(ccdf_data[state][0]) for state in ccdf_data if state != 'all')
    
    if 'green' in ccdf_data:
        x, y = ccdf_data['green']
        pct = len(x) / total_days * 100 if total_days > 0 else 0
        ax1.scatter(x, y, color='green', alpha=0.6, s=50,
                   label=f'GREEN state ({len(x)} days, {pct:.1f}%)',
                   edgecolors='darkgreen', linewidth=0.5, zorder=3)
    
    if 'orange' in ccdf_data:
        x, y = ccdf_data['orange']
        pct = len(x) / total_days * 100 if total_days > 0 else 0
        ax1.scatter(x, y, color='orange', alpha=0.8, s=80,
                   label=f'ORANGE state ({len(x)} days, {pct:.1f}%)',
                   edgecolors='darkorange', linewidth=0.5, zorder=3)
    
    if 'red' in ccdf_data:
        x, y = ccdf_data['red']
        pct = len(x) / total_days * 100 if total_days > 0 else 0
        ax1.scatter(x, y, color='red', alpha=0.6, s=50,
                   label=f'RED state ({len(x)} days, {pct:.1f}%)',
                   edgecolors='darkred', linewidth=0.5, zorder=3)
    
    # Power law fit
    if 'all' in ccdf_data:
        x_all, y_all = ccdf_data['all']
        valid_mask = (x_all > 0) & (y_all > 0)
        x_valid = x_all[valid_mask]
        y_valid = y_all[valid_mask]
        
        tail_mask = x_valid > 0.5
        if tail_mask.sum() > 1:
            log_x = np.log(x_valid[tail_mask])
            log_y = np.log(y_valid[tail_mask])
            slope, intercept = np.polyfit(log_x, log_y, 1)
            alpha = -slope
            
            x_fit = np.logspace(np.log10(0.01), np.log10(30), 100)
            y_fit = np.exp(intercept) * x_fit ** slope
            ax1.plot(x_fit, y_fit, 'k--', linewidth=2.5, alpha=0.7,
                    label=f'Power Law Fit: P(|r| > x) ∝ x^{slope:.2f} (α={alpha:.2f})', zorder=2)
    
    ax1.set_xlabel('Absolute Return Size (%)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('P(|Return| ≥ x)', fontsize=14, fontweight='bold')
    ax1.set_title('CCDF by State (sanity check - should match previous graph)', 
                 fontsize=16, fontweight='bold')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_xlim(xlim)
    ax1.set_ylim([0.01, 1])
    ax1.legend(loc='upper right', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Bottom panel: DERIVATIVE (plot as LINES)
    ax2 = axes[1]
    ax2.axvspan(0.5, 3.0, alpha=0.15, color='blue', zorder=1)
    
    # Plot derivatives as lines
    if 'all' in derivatives:
        x_all = ccdf_data['all'][0]
        ax2.plot(x_all, derivatives['all'], color='black', alpha=0.4, 
                linewidth=2, label='All Returns')
    
    if 'green' in derivatives:
        x_green = ccdf_data['green'][0]
        ax2.plot(x_green, derivatives['green'], color='green', alpha=0.7,
                linewidth=2, label='GREEN')
    
    if 'orange' in derivatives:
        x_orange = ccdf_data['orange'][0]
        ax2.plot(x_orange, derivatives['orange'], color='orange', alpha=0.9,
                linewidth=3, label='ORANGE')
    
    if 'red' in derivatives:
        x_red = ccdf_data['red'][0]
        ax2.plot(x_red, derivatives['red'], color='red', alpha=0.7,
                linewidth=2, label='RED')
    
    # Zero reference line
    ax2.axhline(0, color='black', linestyle='--', alpha=0.3)
    
    ax2.set_xlabel('Absolute Return Size (%)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('d(log CCDF)/d(log x)', fontsize=14, fontweight='bold')
    ax2.set_title('Derivative of CCDF (cut below -0.25)', fontsize=16, fontweight='bold')
    ax2.set_xscale('log')
    ax2.set_xlim(xlim)
    ax2.set_ylim(ylim)
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    if output_path:
        plt.savefig(output_path, dpi=300)
        print(f"✓ Derivative plot saved to {output_path}")
    
    return fig, (ax1, ax2)
