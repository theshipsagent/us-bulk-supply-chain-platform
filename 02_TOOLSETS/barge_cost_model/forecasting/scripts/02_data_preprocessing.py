"""
Data Preprocessing for Barge Rate Forecasting
==============================================

Cleans and prepares weekly barge rate data for VAR/SpVAR modeling.

Steps:
1. Load raw data
2. Handle missing values
3. Test for stationarity
4. Seasonal adjustment
5. Create train/test splits
6. Export processed data

Author: Barge Economics Research Team
Date: February 3, 2026
"""

import sys
import os
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.seasonal import seasonal_decompose
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path("G:/My Drive/LLM/project_barge/forecasting")
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
PLOTS_DIR = BASE_DIR / "results" / "plots"
LOG_DIR = BASE_DIR / "logs"

# Create directories
for directory in [PROCESSED_DATA_DIR, PLOTS_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Modeling parameters
TRAIN_END_DATE = '2020-12-31'  # Training data up to end of 2020
TEST_START_DATE = '2021-01-01'  # Test data starts 2021

print("=" * 70)
print("BARGE RATE DATA PREPROCESSING")
print("=" * 70)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_message(message, level='INFO'):
    """Write log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

    log_file = LOG_DIR / f"preprocessing_log_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def test_stationarity(series, name='Series', alpha=0.05):
    """
    Test time series for stationarity using Augmented Dickey-Fuller test

    H0 (null): Series has unit root (non-stationary)
    H1 (alternative): Series is stationary
    """
    result = adfuller(series.dropna(), autolag='AIC')

    log_message(f"\nStationarity Test: {name}")
    log_message(f"  ADF Statistic: {result[0]:.4f}")
    log_message(f"  p-value: {result[1]:.4f}")
    log_message(f"  Critical Values:")
    for key, value in result[4].items():
        log_message(f"    {key}: {value:.3f}")

    is_stationary = result[1] < alpha
    if is_stationary:
        log_message(f"  ✓ {name} is STATIONARY (p < {alpha})", level='INFO')
    else:
        log_message(f"  ✗ {name} is NON-STATIONARY (p >= {alpha})", level='WARNING')

    return is_stationary, result

def handle_missing_values(df, method='interpolate'):
    """
    Handle missing values in time series data

    Methods:
    - 'interpolate': Linear interpolation
    - 'forward_fill': Forward fill
    - 'drop': Drop missing rows
    """
    log_message(f"\nHandling missing values (method: {method})...")

    missing_before = df.isnull().sum().sum()
    log_message(f"  Missing values before: {missing_before}")

    if method == 'interpolate':
        df = df.interpolate(method='linear', limit_direction='both')
    elif method == 'forward_fill':
        df = df.fillna(method='ffill').fillna(method='bfill')
    elif method == 'drop':
        df = df.dropna()

    missing_after = df.isnull().sum().sum()
    log_message(f"  Missing values after: {missing_after}")
    log_message(f"  ✓ Filled {missing_before - missing_after} missing values")

    return df

def detect_outliers(df, cols, threshold=3.5):
    """
    Detect outliers using modified Z-score method

    Outliers defined as values with modified Z-score > threshold
    """
    log_message(f"\nDetecting outliers (threshold: {threshold} std devs)...")

    outliers_count = 0
    for col in cols:
        median = df[col].median()
        mad = np.median(np.abs(df[col] - median))
        modified_z_scores = 0.6745 * (df[col] - median) / mad

        outliers = np.abs(modified_z_scores) > threshold
        n_outliers = outliers.sum()
        outliers_count += n_outliers

        if n_outliers > 0:
            log_message(f"  {col}: {n_outliers} outliers detected " +
                       f"(max value: ${df.loc[outliers, col].max():.2f})")

    log_message(f"  Total outliers across all segments: {outliers_count}")
    return outliers_count

def create_seasonal_adjustment(df, rate_cols, period=52):
    """
    Perform seasonal decomposition and create seasonally adjusted series

    Uses additive decomposition: Observed = Trend + Seasonal + Residual
    """
    log_message(f"\nPerforming seasonal decomposition (period: {period} weeks)...")

    df_adjusted = df.copy()

    for col in rate_cols:
        # Seasonal decomposition
        decomposition = seasonal_decompose(df[col], model='additive', period=period)

        # Seasonally adjusted = Observed - Seasonal
        df_adjusted[f'{col}_sa'] = df[col] - decomposition.seasonal

        # Calculate seasonal amplitude
        seasonal_amplitude = decomposition.seasonal.max() - decomposition.seasonal.min()
        log_message(f"  {col}: Seasonal amplitude = ${seasonal_amplitude:.2f}/ton")

    log_message(f"  ✓ Created {len(rate_cols)} seasonally adjusted series")
    return df_adjusted, decomposition

# ============================================================================
# MAIN PREPROCESSING PIPELINE
# ============================================================================

def main():
    """Main preprocessing pipeline"""
    log_message("Starting data preprocessing pipeline...")

    # Step 1: Load raw data
    log_message("\n" + "="*70)
    log_message("STEP 1: LOAD RAW DATA")
    log_message("="*70)

    # Find most recent data file
    data_files = list(RAW_DATA_DIR.glob("*.csv"))
    if not data_files:
        log_message("✗ No data files found in raw data directory!", level='ERROR')
        return None

    latest_file = max(data_files, key=lambda p: p.stat().st_mtime)
    log_message(f"Loading: {latest_file.name}")

    df = pd.read_csv(latest_file)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    log_message(f"✓ Loaded {len(df)} observations")
    log_message(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    log_message(f"  Columns: {list(df.columns)}")

    # Identify rate columns
    rate_cols = [c for c in df.columns if '_rate' in c and 'segment' in c]
    log_message(f"  Rate columns: {len(rate_cols)} segments")

    # Step 2: Descriptive statistics
    log_message("\n" + "="*70)
    log_message("STEP 2: DESCRIPTIVE STATISTICS")
    log_message("="*70)

    for col in rate_cols:
        stats_dict = {
            'mean': df[col].mean(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'cv': df[col].std() / df[col].mean()  # Coefficient of variation
        }
        log_message(f"\n{col}:")
        log_message(f"  Mean: ${stats_dict['mean']:.2f}/ton")
        log_message(f"  Std Dev: ${stats_dict['std']:.2f}/ton")
        log_message(f"  Range: ${stats_dict['min']:.2f} - ${stats_dict['max']:.2f}/ton")
        log_message(f"  Coef. of Variation: {stats_dict['cv']:.2f}")

    # Step 3: Handle missing values
    log_message("\n" + "="*70)
    log_message("STEP 3: HANDLE MISSING VALUES")
    log_message("="*70)

    df = handle_missing_values(df[['date', 'week_of_year'] + rate_cols], method='interpolate')

    # Step 4: Detect outliers
    log_message("\n" + "="*70)
    log_message("STEP 4: OUTLIER DETECTION")
    log_message("="*70)

    detect_outliers(df, rate_cols, threshold=3.5)
    log_message("  Note: Outliers NOT removed (may represent real drought/congestion events)")

    # Step 5: Stationarity testing
    log_message("\n" + "="*70)
    log_message("STEP 5: STATIONARITY TESTING")
    log_message("="*70)

    stationarity_results = {}
    for col in rate_cols:
        is_stationary, test_result = test_stationarity(df[col], name=col)
        stationarity_results[col] = is_stationary

    non_stationary_count = sum(1 for v in stationarity_results.values() if not v)
    if non_stationary_count > 0:
        log_message(f"\n  ⚠ {non_stationary_count} segments are non-stationary", level='WARNING')
        log_message("  Consider differencing for VAR modeling", level='WARNING')

    # Step 6: Seasonal decomposition
    log_message("\n" + "="*70)
    log_message("STEP 6: SEASONAL DECOMPOSITION")
    log_message("="*70)

    df_adjusted, decomp = create_seasonal_adjustment(df, rate_cols, period=52)

    # Create plot of seasonal decomposition for first segment
    fig, axes = plt.subplots(4, 1, figsize=(14, 10))
    decomp_example = seasonal_decompose(df[rate_cols[0]], model='additive', period=52)

    df[rate_cols[0]].plot(ax=axes[0], title='Observed')
    decomp_example.trend.plot(ax=axes[1], title='Trend')
    decomp_example.seasonal.plot(ax=axes[2], title='Seasonal')
    decomp_example.resid.plot(ax=axes[3], title='Residual')

    plt.tight_layout()
    plot_file = PLOTS_DIR / '01_seasonal_decomposition_example.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_message(f"\n  ✓ Saved seasonal decomposition plot: {plot_file.name}")
    plt.close()

    # Step 7: Create correlation matrix
    log_message("\n" + "="*70)
    log_message("STEP 7: SPATIAL CORRELATION ANALYSIS")
    log_message("="*70)

    # Correlation matrix
    corr_matrix = df[rate_cols].corr()
    log_message("\nPairwise correlations between segments:")
    log_message(f"\n{corr_matrix.to_string()}")

    # Plot correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
                center=0, vmin=-1, vmax=1, ax=ax, cbar_kws={'label': 'Correlation'})
    ax.set_title('Spatial Correlation: Barge Rates Across River Segments',
                 fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plot_file = PLOTS_DIR / '02_spatial_correlation_matrix.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_message(f"  ✓ Saved correlation heatmap: {plot_file.name}")
    plt.close()

    avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
    log_message(f"\n  Average pairwise correlation: {avg_corr:.3f}")
    if avg_corr > 0.7:
        log_message("  ✓ Strong spatial correlation → SpVAR model appropriate", level='INFO')

    # Step 8: Train/Test split
    log_message("\n" + "="*70)
    log_message("STEP 8: TRAIN/TEST SPLIT")
    log_message("="*70)

    df_train = df_adjusted[df_adjusted['date'] <= TRAIN_END_DATE].copy()
    df_test = df_adjusted[df_adjusted['date'] >= TEST_START_DATE].copy()

    log_message(f"\nTraining set:")
    log_message(f"  Observations: {len(df_train)}")
    log_message(f"  Date range: {df_train['date'].min()} to {df_train['date'].max()}")

    log_message(f"\nTest set:")
    log_message(f"  Observations: {len(df_test)}")
    log_message(f"  Date range: {df_test['date'].min()} to {df_test['date'].max()}")

    # Step 9: Export processed data
    log_message("\n" + "="*70)
    log_message("STEP 9: EXPORT PROCESSED DATA")
    log_message("="*70)

    # Full dataset
    output_file_full = PROCESSED_DATA_DIR / "barge_rates_processed_full.csv"
    df_adjusted.to_csv(output_file_full, index=False)
    log_message(f"✓ Saved full processed dataset: {output_file_full.name}")

    # Training set
    output_file_train = PROCESSED_DATA_DIR / "barge_rates_train.csv"
    df_train.to_csv(output_file_train, index=False)
    log_message(f"✓ Saved training set: {output_file_train.name}")

    # Test set
    output_file_test = PROCESSED_DATA_DIR / "barge_rates_test.csv"
    df_test.to_csv(output_file_test, index=False)
    log_message(f"✓ Saved test set: {output_file_test.name}")

    # Metadata
    metadata = {
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_file': latest_file.name,
        'total_observations': len(df),
        'training_observations': len(df_train),
        'test_observations': len(df_test),
        'rate_columns': rate_cols,
        'stationarity_results': stationarity_results,
        'average_correlation': float(avg_corr),
        'train_end_date': TRAIN_END_DATE,
        'test_start_date': TEST_START_DATE
    }

    import json
    metadata_file = PROCESSED_DATA_DIR / "preprocessing_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    log_message(f"✓ Saved metadata: {metadata_file.name}")

    # Summary
    log_message("\n" + "="*70)
    log_message("PREPROCESSING COMPLETE")
    log_message("="*70)
    log_message(f"\n✓ Data ready for VAR/SpVAR modeling")
    log_message(f"  Training observations: {len(df_train)}")
    log_message(f"  Test observations: {len(df_test)}")
    log_message(f"  Segments: {len(rate_cols)}")
    log_message(f"  Spatial correlation: {avg_corr:.3f}")
    log_message(f"\nNext step: Run 03_var_estimation.py")

    return df_adjusted, df_train, df_test

if __name__ == "__main__":
    result = main()

    if result is not None:
        print("\n" + "=" * 70)
        print("Preprocessing successful! Ready for VAR modeling.")
        print("=" * 70)
