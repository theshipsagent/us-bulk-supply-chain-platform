# Implementation Toolkit: Barge Transportation Econometrics

## SECTION 1: READY-TO-USE DATASETS & HISTORICAL BENCHMARKS

### Historical Barge Rate Benchmarks (1976 Reference System)

**Industry-Standard River Segment Benchmarks:**

```csv
River_Segment,Benchmark_Rate_1976,2023_Usage_Status,Typical_Current_Rate_Range
Twin Cities,$6.19/ton,Active,$12-30/ton (200-500% tariff)
Mid-Mississippi,$5.32/ton,Active,$12-30/ton (200-500% tariff)
St. Louis,$3.99/ton,Active,$10-25/ton (250-600% tariff)
Illinois River,$4.64/ton,Active,$12-32/ton (300-700% tariff)
Cincinnati,$4.69/ton,Active,$12-28/ton (250-600% tariff)
Lower Ohio,$4.46/ton,Active,$12-28/ton (250-600% tariff)
Cairo-Memphis,$3.14/ton,Active,$10-20/ton (300-600% tariff)
```

**Usage Formula:**
```
Current_Rate = (Tariff_Percentage / 100) × Benchmark_Rate
Example: 350% tariff at St. Louis = (350/100) × $3.99 = $13.965/ton
```

---

### 2023 Tonnage Snapshot (USACE Data)

```csv
Commodity,Million_Short_Tons,Percent_of_Total,Primary_Route
Petroleum & Products,135.5,30.2%,Lower Mississippi + Intracoastal
Chemicals,48.0,10.7%,Lower Mississippi + Gulf
Food & Farm Products,73.3,16.3%,Mississippi System → Gulf Export
Coal,Variable (declining),↓,Ohio River declining
Metals & Minerals,50+,11.2%,All river systems
Construction Materials,15+,3.4%,Regional waterways
Other,80+,17.9%,Various

Total Internal (2023): 449 million st
Decline from 2007: 622 → 449 million st (-28%)
```

---

## SECTION 2: PYTHON IMPLEMENTATION TEMPLATES

### 1. Basic Barge Rate Calculation

```python
# Barge Rate Calculator - Industry Standard Percent-of-Tariff System

class BargeTariffCalculator:
    """Calculate barge rates using 1976 benchmark system"""
    
    # 1976 ICC Tariff No. 7 Benchmarks (reference rates)
    BENCHMARKS = {
        'Twin Cities': 6.19,
        'Mid-Mississippi': 5.32,
        'St. Louis': 3.99,
        'Illinois': 4.64,
        'Cincinnati': 4.69,
        'Lower Ohio': 4.46,
        'Cairo-Memphis': 3.14
    }
    
    @classmethod
    def calculate_rate(cls, tariff_percentage, river_segment):
        """
        Calculate actual barge rate from tariff percentage
        
        Args:
            tariff_percentage (float): Current market rate as % of 1976 benchmark
            river_segment (str): River location
            
        Returns:
            float: Barge rate in $/ton
        """
        if river_segment not in cls.BENCHMARKS:
            raise ValueError(f"Unknown river segment: {river_segment}")
        
        benchmark = cls.BENCHMARKS[river_segment]
        rate = (tariff_percentage / 100) * benchmark
        return round(rate, 2)
    
    @classmethod
    def calculate_tariff_percentage(cls, actual_rate, river_segment):
        """Reverse calculation: get tariff % from actual rate"""
        if river_segment not in cls.BENCHMARKS:
            raise ValueError(f"Unknown river segment: {river_segment}")
        
        benchmark = cls.BENCHMARKS[river_segment]
        tariff_pct = (actual_rate / benchmark) * 100
        return round(tariff_pct, 1)

# USAGE EXAMPLES
calc = BargeTariffCalculator()

# Example 1: Calculate rate from tariff percentage
rate = calc.calculate_rate(tariff_percentage=400, river_segment='St. Louis')
print(f"400% tariff at St. Louis = ${rate}/ton")
# Output: 400% tariff at St. Louis = $15.96/ton

# Example 2: Calculate tariff from known rate
tariff = calc.calculate_tariff_percentage(actual_rate=20.00, river_segment='Illinois')
print(f"$20/ton at Illinois = {tariff}% of tariff")
# Output: $20/ton at Illinois = 431.5% of tariff

# Example 3: Create rate lookup for all segments
print("\nCurrent Example Rates (300% tariff):")
for segment in calc.BENCHMARKS.keys():
    rate = calc.calculate_rate(300, segment)
    print(f"  {segment}: ${rate}/ton")
```

---

### 2. Vector Autoregressive (VAR) Model for Rate Forecasting

```python
# VAR Model Implementation for Barge Rate Forecasting
# Following Wetzstein et al. (2021) methodology

import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.var_model import VAR
from sklearn.metrics import mean_squared_error, mean_absolute_error

class BargeForecastingVAR:
    """
    Vector Autoregressive model for 5 river segment barge rates
    Based on Wetzstein et al. (2021) Mississippi River analysis
    """
    
    def __init__(self, data_weekly_rates, lag_order=4):
        """
        Args:
            data_weekly_rates (pd.DataFrame): Weekly rates for 5 river segments
                Columns: ['Twin_Cities', 'Mid_Miss', 'St_Louis', 'Illinois', 'Cincinnati']
            lag_order (int): VAR lag order (typically 4-6 weeks)
        """
        self.data = data_weekly_rates
        self.lag_order = lag_order
        self.model = None
        self.results = None
        
    def fit_model(self):
        """Fit VAR model to weekly rate data"""
        self.model = VAR(self.data)
        self.results = self.model.fit(self.lag_order)
        print(f"VAR Model Fitted (lag={self.lag_order})")
        print(self.results.summary())
        
    def forecast_one_week(self, steps=1):
        """Generate 1-5 week ahead forecast"""
        if self.results is None:
            raise ValueError("Model not fitted. Call fit_model() first.")
        
        forecast = self.results.get_forecast(steps=steps)
        return forecast.fcast
    
    def evaluate_forecast(self, test_data):
        """
        Evaluate forecast accuracy on out-of-sample data
        
        Args:
            test_data (pd.DataFrame): Test set with same columns as training
            
        Returns:
            dict: MAE, RMSE, MAPE for each segment
        """
        forecast = self.forecast_one_week(steps=len(test_data))
        
        metrics = {}
        for col in self.data.columns:
            mae = mean_absolute_error(test_data[col], forecast[:, list(self.data.columns).index(col)])
            rmse = np.sqrt(mean_squared_error(test_data[col], forecast[:, list(self.data.columns).index(col)]))
            mape = np.mean(np.abs((test_data[col] - forecast[:, list(self.data.columns).index(col)]) / test_data[col])) * 100
            
            metrics[col] = {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}
        
        return metrics

# USAGE EXAMPLE
# Assuming weekly_rates_df is a DataFrame with columns for each segment
# Load real data from USDA AMS Grain Transportation Report
var_model = BargeForecastingVAR(data_weekly_rates=weekly_rates_df, lag_order=4)
var_model.fit_model()

# Forecast next 5 weeks
five_week_forecast = var_model.forecast_one_week(steps=5)
print(five_week_forecast)

# Evaluate on test data
test_metrics = var_model.evaluate_forecast(test_data=test_rates_df)
for segment, metrics in test_metrics.items():
    print(f"{segment}: MAE=${metrics['MAE']:.2f}, RMSE=${metrics['RMSE']:.2f}")
```

---

### 3. Spatial Vector Autoregressive (SpVAR) Model

```python
# Spatial VAR - Incorporates spatial interdependence between river segments
# Following Wetzstein et al. (2021) SpVAR methodology

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

class SpatialVARBarge:
    """
    Spatial VAR model for barge rates with spatial weight matrix
    Captures interaction between geographically linked segments
    """
    
    # River segment coordinates (approximate mile markers along Mississippi)
    SEGMENT_COORDINATES = {
        'Twin_Cities': (874, 420),         # mile marker, latitude proxy
        'Mid_Mississippi': (514, 450),
        'St_Louis': (357, 400),
        'Illinois': (464, 350),
        'Cincinnati': (469, 300),
        'Lower_Ohio': (446, 250),
        'Cairo_Memphis': (314, 200)
    }
    
    def __init__(self, data_weekly_rates, lag_order=4, weight_type='inverse_distance'):
        """
        Args:
            data_weekly_rates (pd.DataFrame): Weekly rates for river segments
            lag_order (int): VAR lag order
            weight_type (str): 'inverse_distance' or 'nearest_neighbor'
        """
        self.data = data_weekly_rates
        self.lag_order = lag_order
        self.weight_type = weight_type
        self.W = None  # Spatial weight matrix
        self.segment_order = list(data_weekly_rates.columns)
        
    def create_spatial_weight_matrix(self, phi=1):
        """
        Create spatial weight matrix (row-standardized)
        
        Args:
            phi (int): Distance decay parameter (typically 1 or 2)
        """
        segments = self.segment_order
        coords = np.array([self.SEGMENT_COORDINATES.get(seg, (0,0)) for seg in segments])
        
        # Calculate pairwise distances
        distances = cdist(coords, coords, metric='euclidean')
        
        # Inverse distance weights
        W = np.zeros_like(distances, dtype=float)
        for i in range(len(segments)):
            for j in range(len(segments)):
                if i != j:
                    W[i, j] = 1 / (distances[i, j] ** phi)
        
        # Row-standardize: each row sums to 1
        row_sums = W.sum(axis=1, keepdims=True)
        W = W / row_sums
        
        self.W = W
        return W
    
    def estimate_spvar_simple(self):
        """
        Simplified SpVAR estimation
        Uses OLS with spatial lag term: R_t = AR_t-1 + ρ(W⊗R_t) + ε_t
        """
        if self.W is None:
            self.create_spatial_weight_matrix()
        
        n_segments = self.data.shape[1]
        n_obs = self.data.shape[0]
        
        # Prepare lagged variables
        y = self.data.iloc[self.lag_order:].values  # dependent variable
        
        # Spatial lag term: W ⊗ R_t (Kronecker product structure)
        spatial_lags = []
        for t in range(self.lag_order, n_obs):
            spatial_lag = self.W @ self.data.iloc[t].values
            spatial_lags.append(spatial_lag)
        
        spatial_lags = np.array(spatial_lags)
        
        # Combine with regular VAR lags
        lags = []
        for lag in range(1, self.lag_order + 1):
            lags.append(self.data.iloc[self.lag_order-lag:-lag if lag else None].values)
        
        X = np.column_stack(lags + [spatial_lags])
        
        # OLS estimation
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        
        return beta, spatial_lags

# USAGE
spatial_var = SpatialVARBarge(data_weekly_rates=weekly_rates_df, lag_order=4)
spatial_var.create_spatial_weight_matrix(phi=1)

# Estimate SpVAR coefficients
coefficients, spatial_effects = spatial_var.estimate_spvar_simple()
print(f"Estimated SpVAR coefficients shape: {coefficients.shape}")
```

---

## SECTION 3: R IMPLEMENTATION TEMPLATES

### Basic VAR Model (R with vars package)

```r
# VAR Model in R using "vars" package
# Install: install.packages("vars")

library(vars)
library(tidyverse)

# Load USDA Grain Transportation data
# Example structure: weekly rates for 7 river segments
barge_rates <- read.csv("weekly_barge_rates.csv", 
                        row.names = 1, 
                        stringsAsFactors = FALSE)

# Convert to ts object (weekly data)
barge_ts <- ts(barge_rates, frequency = 52, start = c(2003, 1))

# Fit VAR model with 4 lags
var_model <- VAR(barge_ts, p = 4, type = "const")

# View summary
summary(var_model)

# Forecast next 5 weeks
forecast_5w <- predict(var_model, n.ahead = 5)

# Extract point forecasts
forecast_df <- as.data.frame(forecast_5w$fcst) %>%
  map_df(~.x$fcst)

# Plot forecasts
plot(forecast_5w)

# Evaluate on out-of-sample data (last 20 weeks)
var_train <- VAR(barge_ts[1:(nrow(barge_ts)-20),], p=4, type="const")
predictions <- predict(var_train, n.ahead = 20)
actual <- barge_ts[(nrow(barge_ts)-19):nrow(barge_ts),]

# Calculate RMSE
rmse <- sqrt(mean((predictions$fcst - actual)^2))
print(paste("RMSE:", round(rmse, 2)))
```

---

## SECTION 4: COST CALCULATION SPREADSHEET TEMPLATE

### Excel/CSV Template for Barge Cost Analysis

```csv
Barge_Operation_Cost_Analysis,Unit,Q1_2024,Q2_2024,Q3_2024,Q4_2024
Trip_Distance_Miles,miles,1200,1200,1200,1200
Cargo_Weight,tons,1500,1500,1500,1500
Fuel_Consumption_Rate,gal/day,100,100,100,110
Trip_Duration,days,9,9,9,10
Days_in_Queue,days,0.5,0.8,1.2,0.8
Total_Transit_Time,days,9.5,9.8,10.2,10.8

FUEL COSTS
Fuel_Price_per_Gallon,$/gal,3.25,3.40,3.50,3.75
Total_Fuel_Consumed,gallons,975,1020,1100,1210
Total_Fuel_Cost,$,3168.75,3468.00,3850.00,4537.50

LABOR COSTS
Crew_Size,people,8,8,8,8
Daily_Labor_Cost,$,800,800,800,800
Total_Labor_Cost,$,7600,7840,8160,8640

CAPITAL & FIXED COSTS
Daily_Equipment_Cost,$,150,150,150,150
Insurance_per_Trip,$,500,500,500,500
Maintenance_per_Trip,$,300,300,300,300
Total_Fixed_Cost,$,1800,1800,1800,1800

TERMINAL COSTS
Loading_Cost,$,400,400,400,400
Unloading_Cost,$,400,400,400,400
Demurrage_per_Day,$,0,150,300,150
Total_Terminal_Cost,$,800,950,1100,950

ENVIRONMENTAL/OTHER
Surcharges_per_Trip,$,200,200,200,250
Contingency_Reserve,$,400,400,400,400
Total_Other,$,600,600,600,650

TOTAL TRIP COST
Total_Operating_Cost,$,13868.75,14658.00,15510.00,16578.50

COST PER UNIT
Cost_per_Ton,$,9.25,9.77,10.34,11.05
Cost_per_Ton_Mile,$/ton-mile,0.00771,0.00815,0.00862,0.00920

INDEX BENCHMARKS (2003=100)
Fuel_Index,index,142,149,153,164
Labor_Index,index,85,85,85,85
Combined_Cost_Index,index,112,117,122,129
Tariff_% (St. Louis example),tariff_pct,350,380,420,450
Market_Rate_at_StL,$/ton,13.97,15.16,16.76,17.96
Profit_Margin,$/ton,4.72,5.39,6.42,6.91
Margin_Percent,%,34%,35%,38%,38%
```

---

## SECTION 5: DATA ACQUISITION SCRIPTS

### Python: Download USDA Weekly Barge Rates

```python
# Automated USDA Grain Transportation Report Data Download

import pandas as pd
import requests
from datetime import datetime
import json

class USDABargeDataFetcher:
    """Fetch weekly barge rate data from USDA AgTransport portal"""
    
    BASE_URL = "https://agtransport.usda.gov/api/views/deqi-uken/rows.json"
    
    SEGMENTS = {
        'Twin_Cities': 'Twin_Cities',
        'Mid_Mississippi': 'Mid_Mississippi',
        'St. Louis': 'St_Louis',
        'Illinois': 'Illinois_River',
        'Cincinnati': 'Cincinnati',
        'Lower_Ohio': 'Lower_Ohio',
        'Cairo_Memphis': 'Cairo_Memphis'
    }
    
    @classmethod
    def fetch_latest_rates(cls):
        """Fetch most recent weekly barge rates"""
        try:
            response = requests.get(cls.BASE_URL, params={'$limit': 500})
            response.raise_for_status()
            
            data = response.json()
            records = [row['values'] for row in data['data']]
            
            df = pd.DataFrame(records)
            return df
        
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    @classmethod
    def save_to_csv(cls, df, filename=None):
        """Save fetched data to CSV"""
        if filename is None:
            filename = f"barge_rates_{datetime.now().strftime('%Y%m%d')}.csv"
        
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return filename

# USAGE
fetcher = USDABargeDataFetcher()
latest_data = fetcher.fetch_latest_rates()

if latest_data is not None:
    print(latest_data.head())
    fetcher.save_to_csv(latest_data)
```

---

## SECTION 6: KEY FORMULAS FOR RAPID PROTOTYPING

### Lock Delay Cost Formula

```
Cost_of_Lock_Delay = Delay_Hours × (Fuel_Cost_per_Hour + Labor_Cost_per_Hour)

Where:
Fuel_Cost_per_Hour = (Fuel_Burn_Rate_gal/day ÷ 24) × Fuel_Price_$/gal
Labor_Cost_per_Hour = Daily_Labor_Cost ÷ 24

Example Calculation:
Fuel burn: 100 gal/day
Fuel price: $3.50/gal
Labor: $800/day
Delay: 2 hours

Fuel/hr = (100/24) × $3.50 = $14.58/hr
Labor/hr = $800/24 = $33.33/hr
Total hourly cost = $47.91
Delay cost = 2 × $47.91 = $95.82
```

### Draft Depth Capacity Impact

```
Cargo_Capacity = Design_Capacity × (Actual_Draft ÷ Design_Draft)^2

Where:
Design_Capacity = 1500 tons (typical grain barge at 9-ft draft)
Actual_Draft = restricted draft (e.g., 6 feet during low water)
Design_Draft = 9 feet

Example:
Capacity at 6-ft draft = 1500 × (6/9)^2 = 1500 × 0.444 = 666.7 tons
Reduction: 1500 - 667 = 833.3 tons lost (55% reduction)

Cost Impact:
Lost tons × (Market_Rate / Design_Tons) = revenue loss per trip
833.3 tons × ($15/ton / 1500 tons) = $8.33 per ton revenue loss
```

---

## SECTION 7: VALIDATION & QUALITY CHECKS

### Data Quality Checklist

```python
class BargDataValidator:
    """Quality assurance for barge rate and tonnage data"""
    
    @staticmethod
    def check_missing_values(df):
        """Check for missing data"""
        missing = df.isnull().sum()
        return missing[missing > 0]
    
    @staticmethod
    def check_outliers(series, threshold=3):
        """Identify outliers using z-score method"""
        from scipy import stats
        z_scores = np.abs(stats.zscore(series))
        return np.where(z_scores > threshold)[0]
    
    @staticmethod
    def check_rate_range(df, min_rate=5, max_rate=150):
        """Verify rates are within reasonable bounds"""
        out_of_range = df[(df < min_rate) | (df > max_rate)]
        return out_of_range
    
    @staticmethod
    def check_seasonality(series, window=52):
        """Check for consistent weekly patterns"""
        rolling_mean = series.rolling(window).mean()
        rolling_std = series.rolling(window).std()
        return rolling_mean, rolling_std

# USAGE
validator = BargDataValidator()

# Load data
rates = pd.read_csv("barge_rates.csv")

# Run checks
print("Missing values:", validator.check_missing_values(rates))
print("Outliers detected at indices:", validator.check_outliers(rates['St_Louis']))
print("Out of range values:", validator.check_rate_range(rates))
```

---

## SECTION 8: QUICK REFERENCE TABLES

### Fuel Price Scenario Analysis

```
Scenario,$/gal,Fuel_Cost_per_Day,Annual_Increase,Rate_Impact
Low,$2.50,$250,−$18,250,−$1.22/ton
Base,$3.50,$350,—,—
Moderate,$4.00,$400,+$18,250,+$1.22/ton
High,$4.50,$450,+$36,500,+$2.44/ton
Crisis,$5.50,$550,+$73,000,+$4.87/ton
```

### Lock Delay Impact Scenarios

```
Delay_Hours,Cost_per_Barge_Tow,Equivalent_Rate_Increase,Lost_Competitiveness
0,—,—,—
2,$95.82,+$0.06/ton,minimal
6,$287.46,+$0.19/ton,5% cost increase
12,$574.92,+$0.38/ton,10% cost increase
24,$1149.84,+$0.77/ton,20% cost increase
48,$2299.68,+$1.53/ton,40% cost increase
```

---

## SECTION 9: RESOURCES FOR FURTHER DEVELOPMENT

### Recommended Python Libraries

- **Time Series:** `statsmodels`, `pmdarima`, `tensorflow` (LSTM)
- **Spatial Analysis:** `geopandas`, `pysal`, `scikit-spatial`
- **Optimization:** `scipy.optimize`, `pulp`, `pyomo`
- **Data Access:** `requests`, `sodapy` (SODA API)
- **Visualization:** `plotly`, `seaborn`, `folium`

### Recommended R Packages

- **VAR Models:** `vars`
- **Spatial Econometrics:** `sp`, `sf`, `spatialreg`
- **Time Series:** `forecast`, `tsibble`
- **Optimization:** `lpSolve`
- **Data:** `tidyverse`, `data.table`

---

**Document prepared for:** Implementation-ready barge transportation analysis  
**Last updated:** January 2026

