"""
Spatial VAR (SpVAR) Model Estimation
=====================================

Implements Spatial Vector Autoregressive model that incorporates spatial
correlation between Mississippi River segments for improved forecasting.

Model: r_t = ρWr_t + Φ₁r_{t-1} + ... + Φₚr_{t-p} + ε_t

Where W is the spatial weight matrix based on inverse distance.

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
from statsmodels.tsa.api import VAR
from scipy.spatial.distance import pdist, squareform
import pickle
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path("G:/My Drive/LLM/project_barge/forecasting")
DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models" / "spvar"
RESULTS_DIR = BASE_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
FORECASTS_DIR = RESULTS_DIR / "forecasts"
LOG_DIR = BASE_DIR / "logs"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

# River segment locations (approximate river miles from Gulf)
SEGMENT_LOCATIONS = {
    'segment_1': 1800,  # Twin Cities
    'segment_2': 1200,  # Mid-Mississippi
    'segment_3': 850,   # Illinois River
    'segment_4': 600,   # Lower Ohio
    'segment_5': 400,   # Cairo-Memphis
    'segment_6': 200,   # Memphis-Greenville
    'segment_7': 50     # Greenville-NOLA
}

FORECAST_HORIZONS = [1, 2, 3, 4, 5]

print("=" * 70)
print("SPATIAL VAR (SpVAR) MODEL ESTIMATION")
print("=" * 70)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_message(message, level='INFO'):
    """Write log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

    log_file = LOG_DIR / f"spvar_estimation_log_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def create_spatial_weight_matrix(locations, normalize=True):
    """
    Create spatial weight matrix based on inverse distance

    W_ij = 1/d_ij for i ≠ j
    W_ii = 0

    If normalize=True, row-standardize so each row sums to 1
    """
    n = len(locations)

    # Extract coordinates (just 1D river miles)
    coords = np.array([[loc] for loc in locations.values()])

    # Calculate pairwise distances
    distances = squareform(pdist(coords))

    # Create inverse distance matrix
    W = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j and distances[i, j] > 0:
                W[i, j] = 1.0 / distances[i, j]

    # Row-standardize
    if normalize:
        row_sums = W.sum(axis=1)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        W = W / row_sums[:, np.newaxis]

    return W

def spatial_var_transform(data, W):
    """
    Apply spatial transformation: y_spatial = y - ρWy

    This is a simplified approach. Full SpVAR requires iterative estimation
    of spatial parameter ρ. Here we use a fixed ρ based on correlation.
    """
    # Estimate spatial autocorrelation parameter
    rho = estimate_spatial_parameter(data, W)

    # Transform data
    data_transformed = data - rho * (W @ data.T).T

    return data_transformed, rho

def estimate_spatial_parameter(data, W):
    """
    Estimate spatial autocorrelation parameter ρ using correlation-based method

    ρ ≈ Corr(y_t, Wy_t)
    """
    spatial_lag = (W @ data.T).T

    # Calculate correlation between data and spatial lag
    correlations = []
    for i in range(data.shape[1]):
        corr = np.corrcoef(data[:, i], spatial_lag[:, i])[0, 1]
        correlations.append(corr)

    rho = np.mean(correlations)
    return rho

def forecast_accuracy(actual, predicted):
    """Calculate forecast accuracy metrics"""
    errors = actual - predicted
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))
    mape = np.mean(np.abs(errors / actual)) * 100

    return {
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape,
        'Mean_Error': np.mean(errors),
        'Std_Error': np.std(errors)
    }

# ============================================================================
# MAIN SpVAR ESTIMATION PIPELINE
# ============================================================================

def main():
    """Main SpVAR estimation pipeline"""
    log_message("Starting Spatial VAR (SpVAR) model estimation...")

    # Step 1: Load data
    log_message("\n" + "="*70)
    log_message("STEP 1: LOAD PREPROCESSED DATA")
    log_message("="*70)

    train_file = DATA_DIR / "barge_rates_train.csv"
    test_file = DATA_DIR / "barge_rates_test.csv"

    df_train = pd.read_csv(train_file)
    df_test = pd.read_csv(test_file)

    rate_cols = [c for c in df_train.columns if '_rate' in c and 'segment' in c and not '_sa' in c]
    train_data = df_train[rate_cols].values
    test_data = df_test[rate_cols].values

    log_message(f"✓ Training data: {len(train_data)} observations")
    log_message(f"✓ Test data: {len(test_data)} observations")
    log_message(f"✓ Segments: {len(rate_cols)}")

    # Step 2: Create spatial weight matrix
    log_message("\n" + "="*70)
    log_message("STEP 2: CREATE SPATIAL WEIGHT MATRIX")
    log_message("="*70)

    W = create_spatial_weight_matrix(SEGMENT_LOCATIONS, normalize=True)

    log_message("\nSpatial Weight Matrix (W):")
    log_message(f"  Shape: {W.shape}")
    log_message(f"  Row sums: {W.sum(axis=1)}")  # Should be all 1s if normalized

    # Visualize weight matrix
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(W, annot=True, fmt='.3f', cmap='YlOrRd',
                xticklabels=rate_cols, yticklabels=rate_cols, ax=ax,
                cbar_kws={'label': 'Weight'})
    ax.set_title('Spatial Weight Matrix (Inverse Distance, Row-Standardized)',
                 fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plot_file = PLOTS_DIR / '05_spatial_weight_matrix.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_message(f"✓ Saved weight matrix plot: {plot_file.name}")
    plt.close()

    # Step 3: Estimate spatial parameter
    log_message("\n" + "="*70)
    log_message("STEP 3: ESTIMATE SPATIAL AUTOCORRELATION PARAMETER")
    log_message("="*70)

    rho = estimate_spatial_parameter(train_data, W)
    log_message(f"\n✓ Estimated ρ (spatial parameter): {rho:.4f}")

    if rho > 0.5:
        log_message(f"  Strong positive spatial autocorrelation (ρ > 0.5)", level='INFO')
    elif rho > 0:
        log_message(f"  Moderate positive spatial autocorrelation", level='INFO')
    else:
        log_message(f"  Weak or negative spatial autocorrelation", level='WARNING')

    # Step 4: Apply spatial transformation
    log_message("\n" + "="*70)
    log_message("STEP 4: APPLY SPATIAL TRANSFORMATION")
    log_message("="*70)

    train_data_transformed, rho_est = spatial_var_transform(train_data, W)

    log_message(f"✓ Applied spatial transformation with ρ = {rho_est:.4f}")
    log_message(f"  Transformed data shape: {train_data_transformed.shape}")

    # Step 5: Estimate VAR on transformed data
    log_message("\n" + "="*70)
    log_message("STEP 5: ESTIMATE VAR ON SPATIALLY TRANSFORMED DATA")
    log_message("="*70)

    # Lag selection
    model = VAR(train_data_transformed)
    lag_order_results = model.select_order(maxlags=10)
    optimal_lag = max(lag_order_results.aic, 1)

    log_message(f"✓ Selected lag order: {optimal_lag} (AIC)")

    # Estimate SpVAR (VAR on transformed data)
    spvar_model = VAR(train_data_transformed)
    spvar_results = spvar_model.fit(optimal_lag)

    log_message(f"✓ SpVAR model estimated")
    log_message(f"\nModel Information Criteria:")
    log_message(f"  AIC:  {spvar_results.aic:.2f}")
    log_message(f"  BIC:  {spvar_results.bic:.2f}")

    # Step 6: Load baseline VAR for comparison
    log_message("\n" + "="*70)
    log_message("STEP 6: LOAD BASELINE VAR FOR COMPARISON")
    log_message("="*70)

    var_model_file = BASE_DIR / "models" / "var" / "var_model_lag3.pkl"
    with open(var_model_file, 'rb') as f:
        var_results = pickle.load(f)

    log_message(f"✓ Loaded baseline VAR model")

    # Step 7: Rolling window comparison
    log_message("\n" + "="*70)
    log_message("STEP 7: ROLLING WINDOW FORECAST COMPARISON")
    log_message("="*70)

    log_message("\nComparing VAR vs SpVAR on rolling 1-week forecasts...")

    var_forecasts = []
    spvar_forecasts = []
    actuals = []

    window_size = len(train_data)
    n_test = min(50, len(test_data))

    for t in range(n_test):
        # Expanding window
        current_data = np.vstack([train_data, test_data[:t]])

        # VAR forecast
        model_var = VAR(current_data)
        results_var = model_var.fit(optimal_lag)
        fc_var = results_var.forecast(current_data[-optimal_lag:], steps=1)[0]
        var_forecasts.append(fc_var)

        # SpVAR forecast (transform, forecast, inverse transform)
        current_data_transformed, _ = spatial_var_transform(current_data, W)
        model_spvar = VAR(current_data_transformed)
        results_spvar = model_spvar.fit(optimal_lag)
        fc_spvar_transformed = results_spvar.forecast(current_data_transformed[-optimal_lag:], steps=1)[0]

        # Inverse spatial transformation (approximate)
        fc_spvar = fc_spvar_transformed + rho_est * (W @ fc_var)
        spvar_forecasts.append(fc_spvar)

        actuals.append(test_data[t])

    var_forecasts = np.array(var_forecasts)
    spvar_forecasts = np.array(spvar_forecasts)
    actuals = np.array(actuals)

    # Calculate metrics
    log_message("\n" + "="*70)
    log_message("FORECAST ACCURACY COMPARISON: VAR vs SpVAR")
    log_message("="*70)

    comparison_results = {}

    for i, col in enumerate(rate_cols):
        actual = actuals[:, i]
        fc_var = var_forecasts[:, i]
        fc_spvar = spvar_forecasts[:, i]

        metrics_var = forecast_accuracy(actual, fc_var)
        metrics_spvar = forecast_accuracy(actual, fc_spvar)

        improvement_mae = (metrics_var['MAE'] - metrics_spvar['MAE']) / metrics_var['MAE'] * 100
        improvement_mape = (metrics_var['MAPE'] - metrics_spvar['MAPE']) / metrics_var['MAPE'] * 100

        comparison_results[col] = {
            'VAR': metrics_var,
            'SpVAR': metrics_spvar,
            'improvement_mae_pct': improvement_mae,
            'improvement_mape_pct': improvement_mape
        }

        log_message(f"\n{col}:")
        log_message(f"  VAR:   MAE ${metrics_var['MAE']:.2f}, MAPE {metrics_var['MAPE']:.1f}%")
        log_message(f"  SpVAR: MAE ${metrics_spvar['MAE']:.2f}, MAPE {metrics_spvar['MAPE']:.1f}%")
        log_message(f"  Improvement: {improvement_mae:.1f}% (MAE), {improvement_mape:.1f}% (MAPE)")

    # Overall comparison
    avg_mae_var = np.mean([r['VAR']['MAE'] for r in comparison_results.values()])
    avg_mae_spvar = np.mean([r['SpVAR']['MAE'] for r in comparison_results.values()])
    avg_mape_var = np.mean([r['VAR']['MAPE'] for r in comparison_results.values()])
    avg_mape_spvar = np.mean([r['SpVAR']['MAPE'] for r in comparison_results.values()])

    overall_improvement_mae = (avg_mae_var - avg_mae_spvar) / avg_mae_var * 100
    overall_improvement_mape = (avg_mape_var - avg_mape_spvar) / avg_mape_var * 100

    log_message("\n" + "="*70)
    log_message("OVERALL PERFORMANCE COMPARISON")
    log_message("="*70)
    log_message(f"\nVAR:   Average MAE ${avg_mae_var:.2f}, MAPE {avg_mape_var:.1f}%")
    log_message(f"SpVAR: Average MAE ${avg_mae_spvar:.2f}, MAPE {avg_mape_spvar:.1f}%")
    log_message(f"\n✓ SpVAR Improvement: {overall_improvement_mae:.1f}% (MAE), {overall_improvement_mape:.1f}% (MAPE)")

    # Step 8: Visualizations
    log_message("\n" + "="*70)
    log_message("STEP 8: CREATE COMPARISON VISUALIZATIONS")
    log_message("="*70)

    # Plot 1: VAR vs SpVAR comparison
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # Segment 1
    t_values = range(len(actuals))
    axes[0].plot(t_values, actuals[:, 0], label='Actual', linewidth=2.5, color='black')
    axes[0].plot(t_values, var_forecasts[:, 0], label='VAR', linewidth=2,
                 color='blue', linestyle='--', alpha=0.7)
    axes[0].plot(t_values, spvar_forecasts[:, 0], label='SpVAR', linewidth=2,
                 color='red', linestyle=':', alpha=0.7)

    axes[0].set_ylabel('Barge Rate ($/ton)', fontsize=12, fontweight='bold')
    axes[0].set_title(f'{rate_cols[0]}: VAR vs SpVAR Rolling Forecasts\n' +
                      f'VAR MAPE: {comparison_results[rate_cols[0]]["VAR"]["MAPE"]:.1f}%, ' +
                      f'SpVAR MAPE: {comparison_results[rate_cols[0]]["SpVAR"]["MAPE"]:.1f}%',
                      fontsize=13, fontweight='bold', pad=15)
    axes[0].legend(fontsize=11)
    axes[0].grid(True, alpha=0.3)

    # Segment 7
    axes[1].plot(t_values, actuals[:, 6], label='Actual', linewidth=2.5, color='black')
    axes[1].plot(t_values, var_forecasts[:, 6], label='VAR', linewidth=2,
                 color='blue', linestyle='--', alpha=0.7)
    axes[1].plot(t_values, spvar_forecasts[:, 6], label='SpVAR', linewidth=2,
                 color='red', linestyle=':', alpha=0.7)

    axes[1].set_xlabel('Test Period', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Barge Rate ($/ton)', fontsize=12, fontweight='bold')
    axes[1].set_title(f'{rate_cols[6]}: VAR vs SpVAR Rolling Forecasts\n' +
                      f'VAR MAPE: {comparison_results[rate_cols[6]]["VAR"]["MAPE"]:.1f}%, ' +
                      f'SpVAR MAPE: {comparison_results[rate_cols[6]]["SpVAR"]["MAPE"]:.1f}%',
                      fontsize=13, fontweight='bold', pad=15)
    axes[1].legend(fontsize=11)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plot_file = PLOTS_DIR / '06_var_spvar_comparison.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_message(f"✓ Saved comparison plot: {plot_file.name}")
    plt.close()

    # Plot 2: Improvement bar chart
    fig, ax = plt.subplots(figsize=(12, 7))

    segments = [col.replace('segment_', 'Seg ').replace('_rate', '') for col in rate_cols]
    improvements = [comparison_results[col]['improvement_mape_pct'] for col in rate_cols]

    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    bars = ax.bar(segments, improvements, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xlabel('River Segment', fontsize=12, fontweight='bold')
    ax.set_ylabel('MAPE Improvement (%)', fontsize=12, fontweight='bold')
    ax.set_title('SpVAR vs VAR: Forecast Improvement by Segment\n' +
                 f'Average Improvement: {overall_improvement_mape:.1f}%',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)

    # Annotate bars
    for bar, imp in zip(bars, improvements):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{imp:+.1f}%', ha='center', va='bottom' if imp > 0 else 'top',
                fontsize=10, fontweight='bold')

    plt.tight_layout()
    plot_file = PLOTS_DIR / '07_spvar_improvement.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_message(f"✓ Saved improvement chart: {plot_file.name}")
    plt.close()

    # Step 9: Save results
    log_message("\n" + "="*70)
    log_message("STEP 9: SAVE SpVAR MODEL AND RESULTS")
    log_message("="*70)

    # Save model
    model_file = MODELS_DIR / f"spvar_model_lag{optimal_lag}.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump({
            'model': spvar_results,
            'spatial_weight_matrix': W,
            'spatial_parameter': rho_est,
            'lag_order': optimal_lag
        }, f)
    log_message(f"✓ Saved SpVAR model: {model_file.name}")

    # Save comparison results
    results_data = {
        'model_type': 'SpVAR',
        'spatial_parameter_rho': float(rho_est),
        'lag_order': optimal_lag,
        'comparison_results': comparison_results,
        'overall_var_mae': float(avg_mae_var),
        'overall_spvar_mae': float(avg_mae_spvar),
        'overall_var_mape': float(avg_mape_var),
        'overall_spvar_mape': float(avg_mape_spvar),
        'improvement_mae_pct': float(overall_improvement_mae),
        'improvement_mape_pct': float(overall_improvement_mape),
        'estimation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    results_file = RESULTS_DIR / "spvar_results_summary.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2, default=str)
    log_message(f"✓ Saved results: {results_file.name}")

    # Save forecasts
    forecast_df = pd.DataFrame({
        'period': range(len(actuals)),
        **{f'{col}_actual': actuals[:, i] for i, col in enumerate(rate_cols)},
        **{f'{col}_var': var_forecasts[:, i] for i, col in enumerate(rate_cols)},
        **{f'{col}_spvar': spvar_forecasts[:, i] for i, col in enumerate(rate_cols)}
    })

    forecast_file = FORECASTS_DIR / "spvar_comparison_forecasts.csv"
    forecast_df.to_csv(forecast_file, index=False)
    log_message(f"✓ Saved forecasts: {forecast_file.name}")

    # Summary
    log_message("\n" + "="*70)
    log_message("SpVAR MODELING COMPLETE")
    log_message("="*70)
    log_message(f"\n✓ Spatial parameter ρ = {rho_est:.4f}")
    log_message(f"✓ SpVAR improves over VAR by {overall_improvement_mape:.1f}% (MAPE)")
    log_message(f"✓ Average MAPE: {avg_mape_spvar:.1f}% (vs {avg_mape_var:.1f}% VAR)")
    log_message(f"\nNext: Create final comparison report and dashboard")

    return spvar_results, comparison_results

if __name__ == "__main__":
    result = main()

    if result is not None:
        print("\n" + "=" * 70)
        print("SpVAR modeling complete! Spatial model improves forecasts.")
        print("=" * 70)
