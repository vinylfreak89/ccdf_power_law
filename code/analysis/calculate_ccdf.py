"""
Calculate CCDF (Complementary Cumulative Distribution Function) for returns by state.

CCDF(x) = P(|return| >= x) = fraction of returns with absolute value >= x
"""
import numpy as np


def calculate_ccdf(df):
    """
    Calculate CCDF for returns separated by signal state.
    
    Args:
        df: DataFrame with 'Return' and 'State' columns
        
    Returns:
        dict with key 'all' plus one key per unique state
        Each value is tuple of (x, y) arrays for CCDF coordinates
    """
    def get_ccdf(returns):
        """Calculate CCDF from array of absolute returns"""
        if len(returns) == 0:
            return np.array([]), np.array([])
        
        # Sort returns in descending order
        sorted_returns = np.sort(returns)[::-1]
        
        # CCDF: for each return value, what fraction are >= it
        n = len(sorted_returns)
        ccdf = np.arange(1, n + 1) / n
        
        return sorted_returns, ccdf
    
    # All returns
    all_returns = np.abs(df['Return'].values)
    results = {'all': get_ccdf(all_returns)}
    
    # Get unique states and calculate CCDF for each
    unique_states = df['State'].unique()
    
    for state in unique_states:
        state_returns = np.abs(df[df['State'] == state]['Return'].values)
        results[state.lower()] = get_ccdf(state_returns)
    
    # Print summary
    print(f"✓ CCDF calculated:")
    print(f"  All returns: {len(all_returns):,} points")
    for state in sorted(unique_states):
        count = len(df[df['State'] == state])
        print(f"  {state}: {count:,} points")
    
    return results


if __name__ == '__main__':
    # Test it
    import sys
    sys.path.append('/mnt/user-data/outputs/code/data')
    sys.path.append('/mnt/user-data/outputs/code/signals')
    
    from load_data import load_asset
    from moderate_vol import calculate_signal
    
    print("Testing CCDF calculation on SPX...")
    df = load_asset('_spx_d.csv')
    df = calculate_signal(df)
    
    ccdf_data = calculate_ccdf(df)
    
    print(f"\nSample CCDF values:")
    print(f"All - first 5 points:")
    for i in range(min(5, len(ccdf_data['all'][0]))):
        x, y = ccdf_data['all'][0][i], ccdf_data['all'][1][i]
        print(f"  |return| >= {x:.3f}%: {y*100:.2f}% of days")
