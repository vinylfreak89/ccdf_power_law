# Power Law Trading Signal Investigation

**Period**: December 2025 - January 2026  
**Status**: Phase 1 & 2 Complete - Multiple signals tested and failed

## Quick Start

```bash
# Test signals (all failed)
cd code/signals
python moderate_vol.py              # Phase 1: moderate volatility (forward-biased)
python power_law_deviation.py       # Phase 1: power law deviation (artifact)
python r2_derivative_regime.py      # Phase 2: R² regime (abandoned - noise)
python alpha_derivative_zscore.py   # Phase 2: alpha derivative (no edge)

# Run backtest
cd ../backtest
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
│   ├── signals/                # Signal generators (3 signals)
│   ├── analysis/               # CCDF, derivatives, fit quality, synthetic VIX
│   ├── backtest/               # Backtesting engine
│   └── plotting/               # Visualization modules
├── data/                       # CSV files (15 assets, 100+ years)
├── plots/                      # All visualizations
│   ├── ccdf/                   # CCDF by signal type
│   ├── derivatives/            # Derivative analysis
│   ├── tests/                  # Synthetic/shuffled data tests
│   ├── comparisons/            # Overlays and comparisons
│   └── fit_quality/            # Fit quality regime analysis
├── docs/                       # Documentation
│   └── WORK_LOG.md             # Complete investigation log
└── tests/                      # Validation scripts
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

**Validation**:
- `code/analysis/test_vs_random.py` - Statistical validation framework

## Summary

### What Failed
✗ Power law deviation signal - mathematical artifact  
✗ Moderate volatility signal - forward bias or broken  
✗ R² derivative - just noise, no predictive power  
✗ Alpha derivative - real pattern but no trading edge (underperforms 64k% vs buy-hold)  
✗ Shorting during stress periods - destroys returns  

### What Works  
✓ Clean modular infrastructure  
✓ Statistical validation framework  
✓ Methodology to detect artifacts  
✓ 15 assets, 100+ years of data  
✓ Rigorous testing process that eliminates false signals

### What We Learned
- Visual patterns can be deceptive (seeing ≠ trading)
- R² correlates 0.74 with VIX but lags crashes
- Alpha oscillator quiets during bear markets but fires too early
- Multiple mathematical approaches measuring same thing (volatility)
- T+1 testing is critical, T+0 is useless

**Status**: Phase 1 & 2 Complete. Ready for Phase 3.

---

*For complete details, read docs/WORK_LOG.md*
