"""
Plot CCDF (Complementary Cumulative Distribution Function) by state.

Creates log-log plot showing power law behavior with different states colored.
Extracted from colored_graph_fixed.py
"""
import matplotlib.pyplot as plt
import numpy as np


def plot_ccdf_by_state(ccdf_data, title='CCDF by State', output_path=None,
                        asset_name='Asset', date_range=None, show_fit=True,
                        fit_range=(0.5, 30), xlim=(0.3, 5), ylim=(0.01, 1),
                        highlight_zone=(0.5, 3.0)):
    """
    Plot CCDF in log-log space, colored by state.
    Uses the exact plotting style from colored_graph_fixed.py
    
    Args:
        ccdf_data: dict from calculate_ccdf() with (x, y) tuples
                   Keys: 'all', 'green', 'red', 'orange' (optional)
        title: Plot title (or None to auto-generate)
        output_path: If provided, save to this path
        asset_name: Name of asset for title
        date_range: Tuple of (start_date, end_date) for title
        show_fit: If True, fit and plot power law line
        fit_range: tuple (min, max) for fitting range in %
        xlim: X-axis limits (min, max)
        ylim: Y-axis limits (min, max)
        highlight_zone: tuple (min, max) to highlight moderate zone
        
    Returns:
        fig, ax objects
    """
    # Create figure with proper spacing (from original)
    fig, ax = plt.subplots(figsize=(20, 12))
    plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.08)
    
    # Plot 'all' data FIRST as background (black, lower alpha)
    if 'all' in ccdf_data:
        x_all, y_all = ccdf_data['all']
        valid = (x_all > 0) & (y_all > 0)
        ax.scatter(x_all[valid], y_all[valid], color='black', alpha=0.3, s=20,
                  label='All Returns (full CCDF)', edgecolors='none', zorder=2)
        
        # Fit power law to all data
        if show_fit:
            # Fit on tail (returns > fit_range[0]), matching original logic
            fit_mask = (x_all > fit_range[0]) & valid
            x_fit = x_all[fit_mask]
            y_fit = y_all[fit_mask]
            
            if len(x_fit) > 1:
                log_x = np.log(x_fit)
                log_y = np.log(y_fit)
                slope, intercept = np.polyfit(log_x, log_y, 1)
                alpha = -slope
                
                # Plot fitted line across wider range than fit
                x_line = np.logspace(np.log10(0.01), np.log10(30), 100)
                y_line = np.exp(intercept) * x_line ** slope
                ax.plot(x_line, y_line, 'k--', linewidth=2.5, alpha=0.7,
                       label=f'Power Law Fit: P(|r| > x) ∝ x^{slope:.2f} (α={alpha:.2f})')
    
    # Count total days for percentages
    total_days = sum(len(ccdf_data[state][0]) for state in ccdf_data if state != 'all')
    
    # Plot GREEN state
    if 'green' in ccdf_data:
        x, y = ccdf_data['green']
        pct = len(x) / total_days * 100 if total_days > 0 else 0
        ax.scatter(x, y, color='green', alpha=0.6, s=50,
                  label=f'GREEN state ({len(x)} days, {pct:.1f}%)',
                  edgecolors='darkgreen', linewidth=0.5, zorder=3)
    
    # Plot ORANGE state (if exists)
    if 'orange' in ccdf_data:
        x, y = ccdf_data['orange']
        pct = len(x) / total_days * 100 if total_days > 0 else 0
        ax.scatter(x, y, color='orange', alpha=0.8, s=80,
                  label=f'ORANGE state ({len(x)} days, {pct:.1f}%)',
                  edgecolors='darkorange', linewidth=0.5, zorder=4)
    
    # Plot RED state
    if 'red' in ccdf_data:
        x, y = ccdf_data['red']
        pct = len(x) / total_days * 100 if total_days > 0 else 0
        ax.scatter(x, y, color='red', alpha=0.6, s=50,
                  label=f'RED state ({len(x)} days, {pct:.1f}%)',
                  edgecolors='darkred', linewidth=0.5, zorder=3)
    
    # Highlight moderate zone
    if highlight_zone:
        ax.axvspan(highlight_zone[0], highlight_zone[1], alpha=0.15, color='blue',
                  zorder=1, label=f'Moderate Volatility Zone ({highlight_zone[0]}-{highlight_zone[1]}%)')
        # Add zone labels
        mid_x = (highlight_zone[0] + highlight_zone[1]) / 2
        ax.text(mid_x, 0.5, 'Most Returns', fontsize=14, ha='center',
               color='gray', style='italic')
        ax.text(0.05, 0.2, 'Rare\nExtreme\nEvents', fontsize=11, ha='left',
               color='gray', style='italic')
    
    # Set scales and labels
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Absolute Return Size (%)', fontsize=16, fontweight='bold')
    ax.set_ylabel('P(|Return| ≥ x)', fontsize=16, fontweight='bold')
    
    # Generate title if not provided
    if title is None and date_range:
        title = f'{asset_name} Power-Law Distribution by Market State ({date_range[0].year}-{date_range[1].year})\n'
        title += 'Moderate Volatility Signal (2-year rolling baseline)'
    elif title is None:
        title = f'{asset_name} Power-Law Distribution by Market State'
    
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    
    # Set limits and grid
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.legend(loc='upper right', fontsize=13, framealpha=0.95)
    ax.grid(True, alpha=0.3, which='both')
    
    if output_path:
        plt.savefig(output_path, dpi=300)
        print(f"✓ CCDF plot saved to {output_path}")
    
    return fig, ax


if __name__ == '__main__':
    print("Module loaded successfully.")
    print("To test: provide ccdf_data dict from calculate_ccdf()")
    print("Example usage:")
    print("  from calculate_ccdf import calculate_ccdf")
    print("  ccdf_data = calculate_ccdf(df)  # df has 'Return' and 'State' columns")
    print("  plot_ccdf_by_state(ccdf_data, output_path='output.png')")
