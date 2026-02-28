"""
VAR Model Estimation for Barge Rate Forecasting
================================================

Implements Vector Autoregressive (VAR) model for multi-step ahead forecasting
of Mississippi River barge freight rates across 7 segments.

Model: r_t = Φ₁r_{t-1} + Φ₂r_{t-2} + ... + Φₚr_{t-p} + ε_t

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
from statsmodels.tsa.stattools import adfuller
import pickle
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path("G:/My Drive/LLM/project_barge/forecasting")
DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models" / "var"
RESULTS_DIR = BASE_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
FORECASTS_DIR = RESULTS_DIR / "forecasts"
LOG_DIR = BASE_DIR / "logs"

# Create directories
for directory in [MODELS_DIR, PLOTS_DIR, FORECASTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Forecasting parameters
MAX_LAG = 10  # Maximum lag to consider
FORECAST_HORIZONS = [1, 2, 3, 4, 5]  # 1-5 weeks ahead

print("=" * 70)
print("VAR MODEL ESTIMATION & FORECASTING")
print("=" * 70)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_message(message, level='INFO'):
    """Write log message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

    log_file = LOG_DIR / f"var_estimation_log_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def calculate_aic_bic(model_results):
    """Calculate AIC and BIC for model selection"""
    return {
        'aic': model_results.aic,
        'bic': model_results.bic,
        'hqic': model_results.hqic,
        'fpe': model_results.fpe
    }

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
# MAIN VAR ESTIMATION PIPELINE
# ============================================================================

def main():
    """Main VAR estimation and forecasting pipeline"""
    log_message("Starting VAR model estimation...")

    # Step 1: Load preprocessed data
    log_message("\n" + "="*70)
    log_message("STEP 1: LOAD PREPROCESSED DATA")
    log_message("="*70)

    train_file = DATA_DIR / "barge_rates_train.csv"
    test_file = DATA_DIR / "barge_rates_test.csv"

    df_train = pd.read_csv(train_file)
    df_test = pd.read_csv(test_file)

    df_train['date'] = pd.to_datetime(df_train['date'])
    df_test['date'] = pd.to_datetime(df_test['date'])

    # Get rate columns
    rate_cols = [c for c in df_train.columns if '_rate' in c and 'segment' in c and not '_sa' in c]
    log_message(f"✓ Loaded training data: {len(df_train)} observations")
    log_message(f"✓ Loaded test data: {len(df_test)} observations")
    log_message(f"✓ Rate columns: {rate_cols}")

    # Prepare data for VAR
    train_data = df_train[rate_cols].values
    test_data = df_test[rate_cols].values

    # Step 2: Lag order selection
    log_message("\n" + "="*70)
    log_message("STEP 2: LAG ORDER SELECTION")
    log_message("="*70)

    model = VAR(train_data)
    lag_order_results = model.select_order(maxlags=MAX_LAG)

    log_message("\nInformation Criteria for Lag Selection:")
    log_message(f"  AIC:  {lag_order_results.aic} lags")
    log_message(f"  BIC:  {lag_order_results.bic} lags")
    log_message(f"  FPE:  {lag_order_results.fpe} lags")
    log_message(f"  HQIC: {lag_order_results.hqic} lags")

    # Use AIC (better for forecasting) with minimum lag of 1
    optimal_lag = max(lag_order_results.aic, 1)  # Ensure at least lag 1
    log_message(f"\n✓ Selected lag order: {optimal_lag} (based on AIC, min 1)")

    # Step 3: Estimate VAR model
    log_message("\n" + "="*70)
    log_message("STEP 3: ESTIMATE VAR MODEL")
    log_message("="*70)

    var_model = VAR(train_data)
    var_results = var_model.fit(optimal_lag)

    log_message(f"✓ VAR({optimal_lag}) model estimated")
    log_message(f"\nModel Information Criteria:")
    log_message(f"  AIC:  {var_results.aic:.2f}")
    log_message(f"  BIC:  {var_results.bic:.2f}")
    log_message(f"  HQIC: {var_results.hqic:.2f}")
    log_message(f"  FPE:  {var_results.fpe:.2f}")

    # Coefficients summary
    log_message(f"\nModel Summary:")
    log_message(f"  Equations: {var_results.neqs}")
    log_message(f"  Parameters per equation: {var_results.k_ar * var_results.neqs + 1}")
    log_message(f"  Total parameters: {var_results.k_ar * var_results.neqs * var_results.neqs + var_results.neqs}")

    # Step 4: Residual diagnostics
    log_message("\n" + "="*70)
    log_message("STEP 4: RESIDUAL DIAGNOSTICS")
    log_message("="*70)

    residuals = var_results.resid

    log_message("\nResidual Statistics:")
    for i, col in enumerate(rate_cols):
        resid_mean = residuals[:, i].mean()
        resid_std = residuals[:, i].std()
        log_message(f"  {col}:")
        log_message(f"    Mean: {resid_mean:.4f} (should be ~0)")
        log_message(f"    Std Dev: {resid_std:.2f}")

    # Serial correlation test (Portmanteau test)
    # Commented out as it requires additional setup
    # log_message("\nPortmanteau test for residual autocorrelation...")

    # Step 5: One-step ahead forecasts (in-sample)
    log_message("\n" + "="*70)
    log_message("STEP 5: IN-SAMPLE FORECAST EVALUATION")
    log_message("="*70)

    # Fitted values (one-step ahead forecasts)
    fitted_values = var_results.fittedvalues

    log_message("\nIn-sample forecast accuracy:")
    for i, col in enumerate(rate_cols):
        actual = train_data[optimal_lag:, i]  # Skip initial lag periods
        predicted = fitted_values[:, i]

        metrics = forecast_accuracy(actual, predicted)
        log_message(f"\n  {col}:")
        log_message(f"    MAE:  ${metrics['MAE']:.2f}/ton")
        log_message(f"    RMSE: ${metrics['RMSE']:.2f}/ton")
        log_message(f"    MAPE: {metrics['MAPE']:.1f}%")

    # Step 6: Out-of-sample forecasts
    log_message("\n" + "="*70)
    log_message("STEP 6: OUT-OF-SAMPLE FORECASTING")
    log_message("="*70)

    # Multi-step ahead forecasts
    forecast_results = {}

    for horizon in FORECAST_HORIZONS:
        log_message(f"\n{horizon}-week ahead forecast:")

        # Forecast
        forecast = var_results.forecast(train_data[-optimal_lag:], steps=horizon)
        last_forecast = forecast[-1]  # Get the h-step ahead forecast

        # Compare with actual test data
        if horizon <= len(test_data):
            actual = test_data[horizon-1]

            # Calculate metrics for each segment
            segment_metrics = {}
            for i, col in enumerate(rate_cols):
                metrics = {
                    'actual': actual[i],
                    'forecast': last_forecast[i],
                    'error': actual[i] - last_forecast[i],
                    'abs_error': abs(actual[i] - last_forecast[i]),
                    'pct_error': abs(actual[i] - last_forecast[i]) / actual[i] * 100
                }
                segment_metrics[col] = metrics

            forecast_results[f'{horizon}_week'] = segment_metrics

            # Log summary
            avg_mae = np.mean([m['abs_error'] for m in segment_metrics.values()])
            avg_mape = np.mean([m['pct_error'] for m in segment_metrics.values()])
            log_message(f"  Average MAE: ${avg_mae:.2f}/ton")
            log_message(f"  Average MAPE: {avg_mape:.1f}%")

    # Step 7: Rolling window forecast evaluation
    log_message("\n" + "="*70)
    log_message("STEP 7: ROLLING WINDOW EVALUATION")
    log_message("="*70)

    # Rolling 1-week ahead forecasts on test set
    rolling_forecasts = []
    rolling_actuals = []

    window_size = len(train_data)
    log_message(f"\nEvaluating rolling 1-week ahead forecasts...")
    log_message(f"  Window size: {window_size} observations")
    log_message(f"  Test periods: {len(test_data)}")

    for t in range(min(50, len(test_data))):  # First 50 test observations
        # Expanding window: add one more observation each time
        current_data = np.vstack([train_data, test_data[:t]])

        # Fit model on current window
        model_temp = VAR(current_data)
        results_temp = model_temp.fit(optimal_lag)

        # 1-week ahead forecast
        fc = results_temp.forecast(current_data[-optimal_lag:], steps=1)

        rolling_forecasts.append(fc[0])
        rolling_actuals.append(test_data[t])

    rolling_forecasts = np.array(rolling_forecasts)
    rolling_actuals = np.array(rolling_actuals)

    # Calculate rolling forecast accuracy
    log_message("\nRolling 1-week ahead forecast accuracy:")
    for i, col in enumerate(rate_cols):
        actual = rolling_actuals[:, i]
        predicted = rolling_forecasts[:, i]

        metrics = forecast_accuracy(actual, predicted)
        log_message(f"\n  {col}:")
        log_message(f"    MAE:  ${metrics['MAE']:.2f}/ton")
        log_message(f"    RMSE: ${metrics['RMSE']:.2f}/ton")
        log_message(f"    MAPE: {metrics['MAPE']:.1f}%")

    # Step 8: Visualizations
    log_message("\n" + "="*70)
    log_message("STEP 8: CREATE VISUALIZATIONS")
    log_message("="*70)

    # Plot 1: Residuals
    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    axes = axes.flatten()

    for i, col in enumerate(rate_cols):
        axes[i].plot(residuals[:, i], alpha=0.7)
        axes[i].axhline(y=0, color='r', linestyle='--', alpha=0.5)
        axes[i].set_title(f'Residuals: {col}', fontsize=10, fontweight='bold')
        axes[i].set_xlabel('Time')
        axes[i].set_ylabel('Residual ($/ton)')
        axes[i].grid(True, alpha=0.3)

    plt.tight_layout()
    plot_file = PLOTS_DIR / '03_var_residuals.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_message(f"✓ Saved residuals plot: {plot_file.name}")
    plt.close()

    # Plot 2: Rolling forecast performance
    fig, ax = plt.subplots(figsize=(14, 7))

    # Plot for first segment
    t_values = range(len(rolling_actuals))
    ax.plot(t_values, rolling_actuals[:, 0], label='Actual', linewidth=2, color='blue')
    ax.plot(t_values, rolling_forecasts[:, 0], label='VAR Forecast', linewidth=2,
            color='red', linestyle='--', alpha=0.7)

    ax.set_xlabel('Test Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Barge Rate ($/ton)', fontsize=12, fontweight='bold')
    ax.set_title(f'VAR Rolling 1-Week Ahead Forecast: {rate_cols[0]}\n' +
                 f'MAE: ${forecast_accuracy(rolling_actuals[:, 0], rolling_forecasts[:, 0])["MAE"]:.2f}/ton',
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_file = PLOTS_DIR / '04_var_rolling_forecast.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_message(f"✓ Saved rolling forecast plot: {plot_file.name}")
    plt.close()

    # Step 9: Save model and results
    log_message("\n" + "="*70)
    log_message("STEP 9: SAVE MODEL AND RESULTS")
    log_message("="*70)

    # Save VAR model
    model_file = MODELS_DIR / f"var_model_lag{optimal_lag}.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump(var_results, f)
    log_message(f"✓ Saved VAR model: {model_file.name}")

    # Save forecast results
    results_data = {
        'model_type': 'VAR',
        'lag_order': optimal_lag,
        'training_observations': len(train_data),
        'test_observations': len(test_data),
        'segments': rate_cols,
        'forecast_horizons': FORECAST_HORIZONS,
        'multi_step_forecasts': forecast_results,
        'model_criteria': calculate_aic_bic(var_results),
        'estimation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    results_file = RESULTS_DIR / "var_results_summary.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2, default=str)
    log_message(f"✓ Saved results summary: {results_file.name}")

    # Save rolling forecasts
    rolling_df = pd.DataFrame({
        'period': range(len(rolling_actuals)),
        **{f'{col}_actual': rolling_actuals[:, i] for i, col in enumerate(rate_cols)},
        **{f'{col}_forecast': rolling_forecasts[:, i] for i, col in enumerate(rate_cols)}
    })

    rolling_file = FORECASTS_DIR / "var_rolling_forecasts.csv"
    rolling_df.to_csv(rolling_file, index=False)
    log_message(f"✓ Saved rolling forecasts: {rolling_file.name}")

    # Summary
    log_message("\n" + "="*70)
    log_message("VAR MODELING COMPLETE")
    log_message("="*70)
    log_message(f"\n✓ VAR({optimal_lag}) model successfully estimated")
    log_message(f"  Training observations: {len(train_data)}")
    log_message(f"  Segments modeled: {len(rate_cols)}")
    log_message(f"  Forecast horizons: {FORECAST_HORIZONS} weeks")
    log_message(f"\nNext step: Run 04_spvar_estimation.py for spatial extension")

    return var_results, forecast_results

if __name__ == "__main__":
    result = main()

    if result is not None:
        print("\n" + "=" * 70)
        print("VAR modeling successful! Ready for SpVAR extension.")
        print("=" * 70)
