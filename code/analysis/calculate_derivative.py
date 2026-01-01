"""
Calculate derivative of CCDF in log-log space.

The derivative d(log(CCDF))/d(log(x)) tells us the local slope of the power law.
For a pure power law P(x) = C*x^(-alpha), the derivative is constant = -alpha.
Changes in the derivative indicate deviations from power law behavior.
"""
import numpy as np


def calculate_derivative(ccdf_data, min_derivative=-10.0):
    """
    Calculate derivative of CCDF in log-log space for each state.
    
    Args:
        ccdf_data: dict from calculate_ccdf() with (x, y) tuples
        min_derivative: Cut off derivatives below this value (removes tail noise)
        
    Returns:
        dict with same keys as ccdf_data
        Each value is tuple of (x_mid, derivative) arrays
    """
    results = {}
    
    for state, (x, y) in ccdf_data.items():
        if len(x) < 2:
            results[state] = (np.array([]), np.array([]))
            continue
        
        # Filter out zeros and very small values to avoid log issues
        valid_mask = (x > 0) & (y > 0)
        x_valid = x[valid_mask]
        y_valid = y[valid_mask]
        
        if len(x_valid) < 2:
            results[state] = (np.array([]), np.array([]))
            continue
        
        # Convert to log space
        log_x = np.log(x_valid)
        log_y = np.log(y_valid)
        
        # Calculate derivative: d(log y)/d(log x)
        # Use midpoints for x values
        d_log_y = np.diff(log_y)
        d_log_x = np.diff(log_x)
        
        # Avoid division by zero
        nonzero_mask = d_log_x != 0
        derivative = np.zeros(len(d_log_x))
        derivative[nonzero_mask] = d_log_y[nonzero_mask] / d_log_x[nonzero_mask]
        
        # Midpoint x values
        x_mid = (x_valid[:-1] + x_valid[1:]) / 2
        
        # Filter out extreme derivatives (tail noise)
        if min_derivative is not None:
            valid_deriv = derivative >= min_derivative
            x_mid = x_mid[valid_deriv]
            derivative = derivative[valid_deriv]
        
        results[state] = (x_mid, derivative)
    
    print(f"✓ Derivatives calculated:")
    for state in sorted(ccdf_data.keys()):
        x_mid, deriv = results[state]
        if len(deriv) > 0:
            print(f"  {state}: {len(deriv):,} points, mean derivative: {np.mean(deriv):.3f}")
        else:
            print(f"  {state}: no valid points")
    
    return results


if __name__ == '__main__':
    # Test it
    import sys
    sys.path.append('/mnt/user-data/outputs/code/data')
    sys.path.append('/mnt/user-data/outputs/code/signals')
    sys.path.append('/mnt/user-data/outputs/code/analysis')
    
    from load_data import load_asset
    from moderate_vol import calculate_signal
    from calculate_ccdf import calculate_ccdf
    
    print("Testing derivative calculation on SPX...")
    df = load_asset('_spx_d.csv')
    df = calculate_signal(df)
    
    ccdf_data = calculate_ccdf(df)
    deriv_data = calculate_derivative(ccdf_data, min_derivative=-5.0)
    
    # Validate: for a power law, derivative should be approximately constant
    print(f"\nSample derivatives in moderate zone (0.5-3%):")
    for state in ['green', 'red']:
        if state in deriv_data:
            x_mid, deriv = deriv_data[state]
            # Find derivatives in moderate zone
            mask = (x_mid >= 0.5) & (x_mid <= 3.0)
            if mask.sum() > 0:
                mod_deriv = deriv[mask]
                print(f"  {state.upper()}: mean={np.mean(mod_deriv):.3f}, std={np.std(mod_deriv):.3f}")
