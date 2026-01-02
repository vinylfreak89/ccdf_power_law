# Power Law Trading Signal Investigation

⚠️ **PROPRIETARY RESEARCH - ALL RIGHTS RESERVED** ⚠️

**This work is NOT open source. All rights reserved.**  
**Unauthorized use, modification, or derivative works are STRICTLY PROHIBITED.**  
**See LICENSE file for full terms. Violations will result in legal action.**

---

**Period**: December 2025 - January 2026  
**Status**: Phases 1, 2 & 3 Complete - Real regime signal found, but non-directional

## Quick Start

```bash
# Test signals
cd code/signals
python moderate_vol.py              # Phase 1: moderate volatility (forward-biased)
python power_law_deviation.py       # Phase 1: power law deviation (artifact)
python r2_derivative_regime.py      # Phase 2: R² regime (abandoned - noise)
python alpha_derivative_zscore.py   # Phase 2: alpha derivative (no edge)

# Phase 3: Mean CCDF deviation empirical tests
cd ../../tests
python test_simple_empirical.py     # Compression before crashes (81% SPX)
python test_directional_prediction.py # Directional analysis (no edge)

# Run backtest
cd ../code/backtest
python backtest_engine.py

# Statistical validation
cd ../analysis
python test_vs_random.py
```

## Directory Structure

```
organized_project/
├── README.md                   # This file
├── code/                       # Modular codebase
│   ├── data/                   # Data loading utilities
│   ├── signals/                # Signal generators (4 signals)
│   ├── analysis/               # CCDF, derivatives, fit quality, drawdowns
│   ├── backtest/               # Backtesting engine
│   └── plotting/               # Visualization modules
├── data/                       # CSV files (15 assets, 100+ years)
├── plots/                      # All visualizations
│   ├── ccdf/                   # CCDF by signal type
│   ├── derivatives/            # Derivative analysis
│   ├── tests/                  # Synthetic/shuffled data tests
│   ├── comparisons/            # Overlays, multi-asset, animations
│   └── fit_quality/            # Fit quality regime analysis
├── docs/                       # Documentation
│   └── WORK_LOG.md             # Complete investigation log (3 phases)
└── tests/                      # Validation scripts & results
    ├── results/                # Phase 3 empirical test results
    └── test_*.py               # Test scripts
```

## Key Files

**Start here**: `docs/WORK_LOG.md` - Complete findings and context

**Phase 1 (Complete - Failures Documented)**:
- `code/signals/moderate_vol.py` - Moderate vol signal (forward-biased)
- `code/signals/power_law_deviation.py` - Power law signal (artifact)
- `plots/tests/` - Proof that power law patterns are mathematical illusions

**Phase 2 (Complete - Failures Documented)**:
- `code/signals/r2_derivative_regime.py` - R² regime signal (abandoned - just noise)
- `code/signals/alpha_derivative_zscore.py` - Alpha derivative signal (real pattern, no edge)
- `code/analysis/fit_quality.py` - Power law fit analysis
- `code/analysis/synthetic_vix.py` - Synthetic VIX calculator
- `code/backtest/backtest_engine.py` - Position sizing & metrics
- `plots/fit_quality/` - All fit quality visualizations

**Phase 3 (Complete - Real Signal, No Direction)**:
- `tests/results/compression_test_results.csv` - SPX crashes preceded by compression (81%)
- `tests/results/directional_analysis_spx.csv` - No directional edge found
- `tests/test_simple_empirical.py` - Empirical compression testing
- `tests/test_directional_prediction.py` - Full directional analysis
- `plots/comparisons/raw_mean_deviation_full.png` - Full 1920-2025 deviation history
- `plots/comparisons/ccdf_deviation_animation.mp4` - CCDF curve morphing visualization

**Validation**:
- `code/analysis/test_vs_random.py` - Statistical validation framework

## Summary

### What Failed
✗ Power law deviation signal - mathematical artifact  
✗ Moderate volatility signal - forward bias or broken  
✗ R² derivative - just noise, no predictive power  
✗ Alpha derivative - real pattern but no trading edge (underperforms 64k% vs buy-hold)  
✗ Shorting during stress periods - destroys returns  

### What Works (But Not Tradeable Yet)
✓ **Mean CCDF deviation** - REAL regime change detector (Phase 3)
  - 81% compressed before SPX crashes vs 55% random periods
  - 86% compressed before rallies
  - **BUT**: Zero directional information, can't distinguish crash from rally
  - Needs combination with directional indicators

### What Actually Works  
✓ Clean modular infrastructure  
✓ Statistical validation framework  
✓ Methodology to detect artifacts  
✓ 15 assets, 100+ years of data  
✓ Rigorous testing process that eliminates false signals
✓ Empirical validation framework (tested crashes, rallies, random periods)

### What We Learned
- Visual patterns can be deceptive (seeing ≠ trading)
- R² correlates 0.74 with VIX but lags crashes
- Alpha oscillator quiets during bear markets but fires too early
- Multiple mathematical approaches measuring same thing (volatility)
- T+1 testing is critical, T+0 is useless
- **Phase 3**: Compression is real but non-directional - detects regime changes without predicting direction
- Real signals can exist but still be non-tradeable without additional components

**Status**: Phases 1, 2 & 3 Complete. Mean CCDF deviation is a real signal but requires directional component to be tradeable.

---

*For complete details, read docs/WORK_LOG.md*
