# Power Law Trading Signal Investigation

**Period**: December 2025 - January 2026  
**Status**: Exploring R² derivative as volatility regime indicator

## Quick Start

```bash
# Test signals
cd code/signals
python moderate_vol.py          # Phase 1: moderate volatility (proven artifact)
python power_law_deviation.py   # Phase 1: power law deviation (proven artifact)
python r2_derivative_regime.py  # Phase 2: fit quality regime (testing)

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

**Phase 1 (Completed - Failures Documented)**:
- `code/signals/moderate_vol.py` - Moderate vol signal (proven forward-biased)
- `code/signals/power_law_deviation.py` - Power law signal (proven artifact)
- `plots/tests/` - Proof that power law patterns are mathematical illusions

**Phase 2 (In Progress - Testing)**:
- `code/signals/r2_derivative_regime.py` - Fit quality regime signal
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
✗ Shorting during stress periods - destroys returns  

### What Works  
✓ Clean modular infrastructure  
✓ Statistical validation framework  
✓ Methodology to detect artifacts  
✓ 15 assets, 100+ years of data  

### What's Being Tested
⧗ R² derivative as regime indicator  
⧗ Global fit quality degradation predicting volatility  
⧗ Levering up when fit improving (preliminary: 3.5x vs buy-hold)  

**Next**: Statistical validation, eliminate bias, test significance

---

*For complete details, read docs/WORK_LOG.md*
