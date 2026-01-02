import sys
sys.path.append('code/data')
from load_data import load_asset
import numpy as np
import pandas as pd

def identify_drawdowns(df, threshold_pct=15):
    """
    Identify drawdown periods and their preceding peaks.
    
    Returns list of dicts with:
    - peak_date: Local max before drawdown
    - trough_date: Bottom of drawdown
    - drawdown_pct: Size of drawdown
    - peak_idx, trough_idx: Indices
    """
    # Calculate running max
    df['Running_Max'] = df['Close'].expanding().max()
    df['Drawdown'] = (df['Close'] - df['Running_Max']) / df['Running_Max'] * 100
    
    drawdowns = []
    in_drawdown = False
    current_peak_idx = 0
    
    for i in range(1, len(df)):
        # New all-time high - potential peak
        if df.iloc[i]['Close'] >= df.iloc[i]['Running_Max']:
            if not in_drawdown:
                current_peak_idx = i
        
        # Check if we crossed threshold
        if df.iloc[i]['Drawdown'] <= -threshold_pct and not in_drawdown:
            in_drawdown = True
            # Find the actual peak before this drawdown
            # Look back from current position to find local max
            lookback_start = max(0, current_peak_idx - 252)  # Look back up to 1 year
            window = df.iloc[lookback_start:i+1]
            peak_idx = window['Close'].idxmax()
            current_peak_idx = peak_idx
        
        # Exiting drawdown (price recovering)
        if in_drawdown and df.iloc[i]['Drawdown'] > -threshold_pct * 0.5:  # Recovered 50% of drawdown
            # Find the trough
            trough_window = df.iloc[current_peak_idx:i+1]
            trough_idx = trough_window['Drawdown'].idxmin()
            
            drawdown_size = df.iloc[trough_idx]['Drawdown']
            
            drawdowns.append({
                'peak_date': df.iloc[current_peak_idx]['Date'],
                'trough_date': df.iloc[trough_idx]['Date'],
                'drawdown_pct': drawdown_size,
                'peak_idx': current_peak_idx,
                'trough_idx': trough_idx
            })
            
            in_drawdown = False
    
    return drawdowns

# Test on SPX
print("Testing drawdown identification on SPX...")
df = load_asset('_spx_d.csv')

drawdowns = identify_drawdowns(df, threshold_pct=15)

print(f"\nFound {len(drawdowns)} drawdowns >= 15%:")
for dd in drawdowns:
    print(f"  Peak: {dd['peak_date'].strftime('%Y-%m-%d')} -> Trough: {dd['trough_date'].strftime('%Y-%m-%d')} ({dd['drawdown_pct']:.1f}%)")

# Check if we captured known bear markets
known_bears = {
    '1929 Crash': ('1929-08-01', '1932-07-01'),
    '1937 Recession': ('1937-03-01', '1938-04-01'),
    '1973-74 Bear': ('1973-01-01', '1974-12-01'),
    '2000 Dot-com': ('2000-03-01', '2002-10-01'),
    '2008 Financial': ('2007-10-01', '2009-03-01'),
}

print("\nChecking known bear markets:")
for name, (start, end) in known_bears.items():
    start_date = pd.to_datetime(start)
    end_date = pd.to_datetime(end)
    
    captured = any(
        pd.to_datetime(dd['peak_date']) <= end_date and 
        pd.to_datetime(dd['trough_date']) >= start_date
        for dd in drawdowns
    )
    print(f"  {name}: {'✓ CAPTURED' if captured else '✗ MISSED'}")

