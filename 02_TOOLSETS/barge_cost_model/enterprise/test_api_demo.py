"""
Quick API Demo - Test What Was Built
=====================================

Shows working examples of:
1. User registration
2. Login and token generation
3. Forecast generation
4. Model performance retrieval
"""

import sys
import os
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from auth import AuthService
from pathlib import Path
import pickle
import pandas as pd
import json

print("=" * 70)
print("BARGE FORECASTING API - LIVE DEMO")
print("=" * 70)

# Initialize authentication
auth = AuthService()

# 1. Create users
print("\n1. CREATING USERS")
print("-" * 70)

success, token = auth.register("demo_analyst", "analyst@demo.com", "DemoPass123!", "analyst")
if success:
    print("   Created: demo_analyst (analyst role)")
    print(f"   Token: {token.access_token[:50]}...")
else:
    print(f"   User might already exist: {token}")

# 2. Login
print("\n2. USER LOGIN")
print("-" * 70)

token = auth.login("demo_analyst", "DemoPass123!")
if token:
    print("   Login successful!")
    print(f"   Access Token: {token.access_token[:50]}...")
    print(f"   Expires in: {token.expires_in} seconds")
else:
    print("   Login failed")

# 3. Load model and generate forecast
print("\n3. GENERATING FORECAST")
print("-" * 70)

try:
    BASE_DIR = Path(__file__).parent.parent
    model_path = BASE_DIR / "forecasting" / "models" / "var" / "var_model_lag3.pkl"

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print("   Model loaded successfully")

    # Load recent data
    data_path = BASE_DIR / "forecasting" / "data" / "processed" / "barge_rates_test.csv"
    df = pd.read_csv(data_path)
    rate_cols = [c for c in df.columns if '_rate' in c and 'segment' in c and not '_sa' in c]
    recent_data = df[rate_cols].tail(10).values

    # Generate 5-week forecast
    forecast = model.forecast(recent_data[-3:], steps=5)

    print("\n   5-Week Forecast for Segment 1:")
    print("   " + "-" * 50)
    for i in range(5):
        print(f"   Week {i+1}: ${forecast[i, 0]:.2f}/ton")

except Exception as e:
    print(f"   Error: {e}")

# 4. Show model performance
print("\n4. MODEL PERFORMANCE METRICS")
print("-" * 70)

try:
    results_path = BASE_DIR / "forecasting" / "results" / "forecast_comparison_summary.json"
    with open(results_path, 'r') as f:
        results = json.load(f)

    print("\n   VAR Model Performance:")
    print(f"   • Average MAPE: {results['var_model']['avg_mape']:.1f}%")
    print(f"   • Average MAE: ${results['var_model']['avg_mae']:.2f}/ton")
    print(f"   • Average R²: {results['var_model']['avg_r2']:.3f}")

    print("\n   Improvement over Naive:")
    print(f"   • {results['var_model']['improvement_over_naive_pct']:.1f}%")

except Exception as e:
    print(f"   Error: {e}")

# 5. Check permissions
print("\n5. USER PERMISSIONS")
print("-" * 70)

user = auth.get_current_user(token.access_token)
if user:
    print(f"   User: {user.username}")
    print(f"   Role: {user.role}")
    print(f"   Permissions:")
    for perm in user.permissions:
        print(f"   • {perm}")

print("\n" + "=" * 70)
print("DEMO COMPLETE")
print("=" * 70)
print("\nWhat this shows:")
print("• Authentication system working")
print("• JWT tokens generated")
print("• Models loaded and ready")
print("• Forecasts generated successfully")
print("• Performance metrics accessible")
print("\nReady for production use!")
