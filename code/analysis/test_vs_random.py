"""
Test a signal against random signals with same state distribution.

Determines if a signal has genuine predictive power or if its performance
could be achieved by random chance.
"""
import numpy as np
import pandas as pd
from backtest import backtest


def generate_random_signal(real_states):
    """
    Generate random State array using proper Markov chain on cluster resampling.
    Preserves exact clustering structure while randomizing sequence.
    
    Strategy:
    1. Extract all clusters from real signal
    2. Calculate Markov transition probabilities between cluster states
    3. Resample clusters following Markov chain
    4. Build sequence from resampled clusters
    5. Truncate/pad to match exact length and counts
    
    Args:
        real_states: Array of actual states from real signal
        
    Returns:
        Random state array with Markov clustering and exact counts
    """
    # Extract all clusters (state, length) from real signal
    clusters = []
    current_state = real_states[0]
    current_len = 1
    
    for s in real_states[1:]:
        if s == current_state:
            current_len += 1
        else:
            clusters.append((current_state, current_len))
            current_state = s
            current_len = 1
    clusters.append((current_state, current_len))
    
    # Get unique states
    unique_states = np.unique(real_states)
    state_to_idx = {state: i for i, state in enumerate(unique_states)}
    n_states = len(unique_states)
    
    # Build list of clusters for each state
    clusters_by_state = {state: [] for state in unique_states}
    for state, length in clusters:
        clusters_by_state[state].append(length)
    
    # Calculate Markov transition matrix
    transition_counts = np.zeros((n_states, n_states))
    for i in range(len(clusters) - 1):
        from_state = state_to_idx[clusters[i][0]]
        to_state = state_to_idx[clusters[i+1][0]]
        transition_counts[from_state, to_state] += 1
    
    # Convert to probabilities
    transition_probs = np.zeros((n_states, n_states))
    for i in range(n_states):
        row_sum = transition_counts[i].sum()
        if row_sum > 0:
            transition_probs[i] = transition_counts[i] / row_sum
        else:
            # If no transitions from this state, uniform
            transition_probs[i] = 1.0 / n_states
    
    # Generate new sequence using Markov resampling
    # Start with random state matching original initial distribution
    initial_state = real_states[0]
    
    new_sequence = []
    current_state = initial_state
    target_length = len(real_states)
    
    # Generate until we have enough days
    while len(new_sequence) < target_length:
        # Sample a cluster length from this state's actual distribution
        cluster_length = np.random.choice(clusters_by_state[current_state])
        
        # Add this cluster to sequence
        for _ in range(cluster_length):
            new_sequence.append(current_state)
            if len(new_sequence) >= target_length:
                break
        
        # Transition to next state using Markov probabilities
        current_idx = state_to_idx[current_state]
        next_state = np.random.choice(unique_states, p=transition_probs[current_idx])
        current_state = next_state
    
    # Truncate to exact length
    new_sequence = np.array(new_sequence[:target_length])
    
    # Adjust counts to be within 0.5% of target (minimal swaps)
    target_counts = {state: (real_states == state).sum() for state in unique_states}
    actual_counts = {state: (new_sequence == state).sum() for state in unique_states}
    
    tolerance = int(target_length * 0.005)  # 0.5% tolerance
    
    # Fix any state that's outside tolerance
    for state in unique_states:
        diff = target_counts[state] - actual_counts[state]
        
        if abs(diff) > tolerance:
            # Need to adjust this state
            if diff > 0:
                # Need more of this state - swap from other states
                for other_state in unique_states:
                    if other_state == state:
                        continue
                    
                    other_excess = actual_counts[other_state] - target_counts[other_state]
                    if other_excess > tolerance:
                        # This state has excess, swap some
                        n_swaps = min(abs(diff), other_excess - tolerance)
                        indices = np.where(new_sequence == other_state)[0]
                        if len(indices) >= n_swaps:
                            swap_indices = np.random.choice(indices, n_swaps, replace=False)
                            new_sequence[swap_indices] = state
                            actual_counts[state] += n_swaps
                            actual_counts[other_state] -= n_swaps
                            diff = target_counts[state] - actual_counts[state]
                            
                            if abs(diff) <= tolerance:
                                break
            
            elif diff < 0:
                # Have too many of this state - swap to states that need more
                for other_state in unique_states:
                    if other_state == state:
                        continue
                    
                    other_deficit = target_counts[other_state] - actual_counts[other_state]
                    if other_deficit > tolerance:
                        # This state needs more
                        n_swaps = min(abs(diff), other_deficit - tolerance)
                        indices = np.where(new_sequence == state)[0]
                        if len(indices) >= n_swaps:
                            swap_indices = np.random.choice(indices, n_swaps, replace=False)
                            new_sequence[swap_indices] = other_state
                            actual_counts[state] -= n_swaps
                            actual_counts[other_state] += n_swaps
                            diff = target_counts[state] - actual_counts[state]
                            
                            if abs(diff) <= tolerance:
                                break
    
    return new_sequence


def _run_single_trial(args):
    """
    Run a single random trial. Designed for parallel execution.
    
    Args:
        args: Tuple of (df, lag, leverage_map, seed)
        
    Returns:
        float: Performance ratio for this trial
    """
    df, lag, leverage_map, seed = args
    
    # Set unique seed for this worker
    np.random.seed(seed)
    
    # Create independent copy and shuffle states
    df_random = df.copy()
    real_states = df['State'].values
    random_states = generate_random_signal(real_states)
    df_random['State'] = random_states
    
    # Backtest
    df_random_bt = backtest(df_random, lag=lag, leverage_map=leverage_map)
    random_ratio = df_random_bt['Strategy_Cumulative'].iloc[-1] / df_random_bt['BH_Cumulative'].iloc[-1]
    
    return random_ratio


def test_vs_random(df, lag=0, n_trials=50, leverage_map=None):
    """
    Test signal against random signals with identical state counts.
    
    Args:
        df: DataFrame with 'Return', 'Date', and 'State' columns
        lag: Backtest lag (0=T+0, 1=T+1, etc.)
        n_trials: Number of random trials to run
        leverage_map: Optional leverage mapping (passed to backtest)
        
    Returns:
        dict with:
            - real_ratio: Real signal performance ratio
            - random_ratios: List of random signal ratios
            - percentile: Percentile of real signal vs random
            - mean_random: Mean of random ratios
            - p_value: Probability real outperforms by chance
    """
    # Get exact state counts from real signal
    state_counts = df['State'].value_counts()
    
    print(f"✓ State counts:")
    for state, count in sorted(state_counts.items()):
        print(f"  {state}: {count:,} days ({count/len(df)*100:.2f}%)")
    
    # Run backtest on real signal
    df_real = backtest(df, lag=lag, leverage_map=leverage_map)
    real_ratio = df_real['Strategy_Cumulative'].iloc[-1] / df_real['BH_Cumulative'].iloc[-1]
    
    print(f"\n✓ Running {n_trials} random trials in parallel...")
    
    # Generate unique seeds for each trial
    import multiprocessing as mp
    base_seed = np.random.randint(0, 1000000)
    
    # Prepare arguments for each trial - each gets independent seed
    trial_args = [(df, lag, leverage_map, base_seed + i) for i in range(n_trials)]
    
    # Run trials in parallel
    n_workers = mp.cpu_count()
    with mp.Pool(n_workers) as pool:
        random_ratios = pool.map(_run_single_trial, trial_args)
    
    print(f"✓ Completed {n_trials} trials using {n_workers} workers")
    
    # Calculate percentile
    percentile = (np.sum(np.array(random_ratios) < real_ratio) / n_trials) * 100
    mean_random = np.mean(random_ratios)
    median_random = np.median(random_ratios)
    
    # Simple p-value: fraction of random trials that beat or match real
    p_value = (np.sum(np.array(random_ratios) >= real_ratio) / n_trials)
    
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Real signal:     {real_ratio:.2f}x")
    print(f"Random median:   {median_random:.2f}x")
    print(f"Random mean:     {mean_random:.2f}x")
    print(f"Percentile:      {percentile:.0f}th")
    print(f"P-value:         {p_value:.4f}")
    
    if percentile >= 95:
        print(f"✓ Signal significantly outperforms random (p < 0.05)")
    elif percentile >= 90:
        print(f"≈ Signal likely outperforms random (p < 0.10)")
    else:
        print(f"✗ Signal does not significantly outperform random")
    
    return {
        'real_ratio': real_ratio,
        'random_ratios': random_ratios,
        'percentile': percentile,
        'median_random': median_random,
        'mean_random': mean_random,
        'p_value': p_value,
        'state_counts': state_counts.to_dict()
    }


if __name__ == '__main__':
    # Test it
    import sys
    sys.path.append('/mnt/user-data/outputs/code/data')
    sys.path.append('/mnt/user-data/outputs/code/signals')
    sys.path.append('/mnt/user-data/outputs/code/analysis')
    
    from load_data import load_asset
    from moderate_vol import calculate_signal
    from state_utils import combine_states
    
    print("Testing signal vs random on SPX...")
    df = load_asset('_spx_d.csv')
    df = calculate_signal(df)
    
    # Combine ORANGE with GREEN
    df = combine_states(df, 'GREEN', ['ORANGE'])
    
    # Filter to valid days
    df_valid = df[df['Baseline'].notna()].copy()
    
    print("\n" + "="*60)
    print("T+0 (same day trading)")
    print("="*60)
    results_t0 = test_vs_random(df_valid, lag=0, n_trials=50)
    
    print("\n\n" + "="*60)
    print("T+1 (next day trading)")
    print("="*60)
    results_t1 = test_vs_random(df_valid, lag=1, n_trials=50)
