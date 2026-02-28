# Mississippi River Barge Rate Forecasting System

**Project Phase:** Phase 2 - Econometric Forecasting Models (Weeks 2-6)
**Started:** February 3, 2026
**Status:** Development in progress

---

## Overview

This directory contains the implementation of Vector Autoregressive (VAR) and Spatial Vector Autoregressive (SpVAR) models for forecasting Mississippi River barge freight rates 1-5 weeks ahead.

**Expected Performance:**
- 17-29% forecast improvement over naïve methods
- $1M+ cost savings over 2-year horizon for mid-size shippers
- Validated on out-of-sample data (2020-2025)

---

## Directory Structure

```
forecasting/
├── data/                    # Historical data and preprocessed series
│   ├── raw/                # Raw downloads from USDA
│   ├── processed/          # Cleaned time series
│   └── external/           # Exogenous variables (fuel, prices)
├── models/                  # Saved model objects
│   ├── var/                # VAR models
│   ├── spvar/              # Spatial VAR models
│   └── baseline/           # Naïve forecast baselines
├── results/                 # Forecast outputs and validation
│   ├── forecasts/          # 5-week ahead predictions
│   ├── metrics/            # Accuracy metrics
│   └── plots/              # Visualization outputs
├── scripts/                 # Implementation code
│   ├── 01_data_download.py         # Fetch USDA weekly rates
│   ├── 02_data_preprocessing.py    # Clean and prepare data
│   ├── 03_var_estimation.py        # Baseline VAR model
│   ├── 04_spvar_estimation.py      # Spatial VAR model
│   ├── 05_forecast_validation.py   # Out-of-sample testing
│   └── 06_cost_savings_analysis.py # Economic impact
└── README.md               # This file
```

---

## Data Sources

### Primary Data: USDA Weekly Barge Rates
**Source:** USDA Agricultural Marketing Service
**URL:** https://agtransport.usda.gov/
**Coverage:** 7 river segments, 2003-2025 (1,100+ weekly observations)
**Segments:**
1. Twin Cities, MN to Mid-Mississippi
2. Mid-Mississippi to St. Louis, MO
3. St. Louis to Cincinnati, OH (Illinois River)
4. Cincinnati to Cairo, IL (Lower Ohio)
5. Cairo to Memphis, TN
6. Memphis to Greenville, MS
7. Greenville to New Orleans, LA

### Exogenous Variables
- **Lock Delays:** USACE Lock Performance Monitoring System (LPMS)
- **Fuel Prices:** EIA Weekly Petroleum Status Report
- **Corn Prices:** USDA NASS Quick Stats
- **Soybean Prices:** USDA NASS Quick Stats
- **Water Levels:** NOAA Advanced Hydrologic Prediction Service

---

## Model Specifications

### VAR (Vector Autoregressive) Model

**Equation:**
```
r_t = Φ₁r_{t-1} + Φ₂r_{t-2} + ... + Φₚr_{t-p} + Βx_t + ε_t
```

Where:
- `r_t`: Vector of barge rates across segments at time t
- `Φᵢ`: Autoregressive coefficient matrices (lag i)
- `p`: Lag order (selected via AIC/BIC, typically 4-6 weeks)
- `x_t`: Exogenous variables (fuel, lock delays, water levels)
- `Β`: Coefficient matrix for exogenous variables
- `ε_t`: Error term (white noise)

**Estimation:** Maximum likelihood with lag selection via information criteria

### SpVAR (Spatial Vector Autoregressive) Model

**Equation:**
```
r_t = ρWr_t + Φ₁r_{t-1} + ... + Φₚr_{t-p} + Βx_t + ε_t
```

Where:
- `ρ`: Spatial autoregressive coefficient
- `W`: Spatial weight matrix (inverse-distance specification)
- All other terms as in VAR

**Spatial Weight Matrix:**
```
W_ij = 1/d_ij  if i ≠ j
W_ij = 0       if i = j
```
- `d_ij`: Distance between river segments i and j (river miles)
- Row-standardized: `Σⱼ W_ij = 1` for all i

**Estimation:** Maximum likelihood with spatial lag term

---

## Validation Framework

### Training/Testing Split
- **Training:** 2003-2020 (884 weeks)
- **Holdout:** 2020-2025 (260 weeks for out-of-sample validation)

### Forecast Horizons
- 1-week ahead
- 2-week ahead
- 3-week ahead
- 4-week ahead
- 5-week ahead

### Performance Metrics
1. **MAE (Mean Absolute Error):** `Σ|y_t - ŷ_t|/n`
2. **RMSE (Root Mean Squared Error):** `√(Σ(y_t - ŷ_t)²/n)`
3. **MAPE (Mean Absolute Percentage Error):** `Σ|y_t - ŷ_t|/y_t/n × 100`
4. **Diebold-Mariano Test:** Statistical test for forecast superiority
5. **Directional Accuracy:** % of forecasts predicting correct direction of change

### Baseline Comparisons
- **Naïve Forecast:** `ŷ_{t+h} = y_t` (no change forecast)
- **Seasonal Naïve:** `ŷ_{t+h} = y_{t-52}` (same week last year)
- **ARIMA:** Univariate time series model per segment

---

## Implementation Steps (In Progress)

### ✅ Phase 1: Setup (Completed)
- [x] Directory structure created
- [x] Documentation framework
- [x] Data source identification

### 🔄 Phase 2: Data Acquisition (Current)
- [ ] Download USDA weekly barge rates (2003-2025)
- [ ] Download exogenous variables (fuel, commodities, water levels)
- [ ] Data quality checks and validation
- [ ] Handle missing values and outliers

### ⏳ Phase 3: Preprocessing
- [ ] Time series decomposition (trend, seasonal, residual)
- [ ] Stationarity testing (Augmented Dickey-Fuller)
- [ ] Differencing if needed
- [ ] Seasonal adjustment

### ⏳ Phase 4: VAR Implementation
- [ ] Lag order selection (AIC, BIC, HQ criteria)
- [ ] VAR estimation (statsmodels)
- [ ] Residual diagnostics
- [ ] Impulse response functions
- [ ] Variance decomposition

### ⏳ Phase 5: SpVAR Implementation
- [ ] Construct spatial weight matrix
- [ ] SpVAR estimation (spatial lag specification)
- [ ] Compare spatial vs. non-spatial models
- [ ] Test spatial coefficient significance

### ⏳ Phase 6: Forecasting
- [ ] Generate 1-5 week ahead forecasts
- [ ] Rolling window validation
- [ ] Confidence intervals (80%, 95%)
- [ ] Forecast combination (VAR + SpVAR)

### ⏳ Phase 7: Validation & Reporting
- [ ] Out-of-sample accuracy metrics
- [ ] Diebold-Mariano tests
- [ ] Economic value analysis (cost savings)
- [ ] Visualization dashboards
- [ ] Final report and documentation

---

## Technical Requirements

### Python Environment
```bash
pip install pandas numpy scipy statsmodels scikit-learn matplotlib seaborn plotly
```

### Key Libraries
- **pandas:** Time series manipulation
- **statsmodels:** VAR/ARIMA estimation
- **scipy:** Statistical tests
- **sklearn:** Preprocessing and validation
- **matplotlib/seaborn:** Static visualizations
- **plotly:** Interactive dashboards

### R Alternative (Optional)
```R
install.packages(c("vars", "sp", "spdep", "forecast", "tseries"))
```

---

## Expected Outputs

### Deliverables
1. **Historical Data Archive:** 2003-2025 weekly rates (7 segments)
2. **Trained Models:** VAR and SpVAR model objects
3. **Forecast Tables:** 5-week ahead predictions with confidence intervals
4. **Validation Report:** Out-of-sample accuracy metrics
5. **Economic Analysis:** Cost savings calculations
6. **Interactive Dashboard:** Streamlit app for forecasts

### Performance Targets (From Literature)
- **Forecast Improvement:** 17-29% over naïve (Wetzstein et al. 2021)
- **Cost Savings:** $1M+ over 2-year horizon (mid-size shipper, 50K tons/year)
- **Spatial Coefficient:** Significant (ρ > 0, p < 0.05) indicating upstream/downstream linkages

---

## References

**Primary Paper:**
- Wetzstein, B., Florax, R., Foster, K., & Binkley, J. (2021). "Transportation costs: Mississippi River barge rates." *Journal of Commodity Markets*, 21(C). DOI: 10.1016/j.jcomm.2019.100123

**Methodology:**
- Wetzstein, B.M. (2015). "Econometric modeling of barge-freight rates on the Mississippi River." Master's thesis, Purdue University.

**Related Work:**
- Yu, T.E., English, B.C., & Menard, R.J. (2016). "Economic Impacts Analysis of Inland Waterway Disruption"
- Isbell, B., McKenzie, A.M., & Brorsen, B.W. (2020). "The cost of forward contracting in the Mississippi barge freight river market"

---

## Contact & Support

**Project:** Mississippi River Barge Transportation Economics
**Phase:** 2 of 4 (Econometric Forecasting)
**Timeline:** Weeks 2-6 (February 2026)
**Status:** In development

*Last Updated: February 3, 2026*
