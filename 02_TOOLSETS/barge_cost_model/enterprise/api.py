"""
REST API for Barge Rate Forecasting
====================================

FastAPI-based REST API providing:
- Forecast retrieval endpoints
- Model management
- Data access
- User authentication
- Rate limiting

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

from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd
import pickle
from pathlib import Path
import numpy as np

# Local imports
from config import get_config
from auth import AuthService, Token, User

config = get_config()
auth_service = AuthService()

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="Barge Rate Forecasting API",
    description="REST API for Mississippi River barge freight rate forecasts",
    version=config.api.api_version,
    docs_url=f"{config.api.api_prefix}/docs",
    redoc_url=f"{config.api.api_prefix}/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ============================================================================
# PYDANTIC MODELS (REQUEST/RESPONSE SCHEMAS)
# ============================================================================

class UserRegistration(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8)
    role: Optional[str] = "viewer"

class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "bearer"
    expires_in: int

class ForecastRequest(BaseModel):
    """Forecast generation request"""
    segment: str = Field(..., description="River segment (e.g., segment_1_rate)")
    horizon: int = Field(1, ge=1, le=5, description="Forecast horizon in weeks")
    model_type: str = Field("var", description="Model type: 'var' or 'spvar'")

class ForecastResponse(BaseModel):
    """Forecast response"""
    segment: str
    forecast_date: datetime
    horizon: int
    model_type: str
    forecasted_rate: float
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None

class HistoricalData(BaseModel):
    """Historical rate data"""
    segment: str
    date: datetime
    rate: float

class ModelPerformance(BaseModel):
    """Model performance metrics"""
    model_type: str
    segment: str
    mae: float
    rmse: float
    mape: float
    r_squared: float

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    api_version: str
    models_loaded: bool

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user = auth_service.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user

async def require_permission(permission: str):
    """Dependency to check user has specific permission"""
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        if not auth_service.role_manager.has_permission(user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return user

    return permission_checker

# ============================================================================
# MODEL LOADING
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "forecasting" / "models"
DATA_DIR = BASE_DIR / "forecasting" / "data"

_models_cache = {}

def load_model(model_type: str):
    """Load and cache model"""
    if model_type in _models_cache:
        return _models_cache[model_type]

    if model_type == "var":
        model_path = MODELS_DIR / "var" / "var_model_lag3.pkl"
    elif model_type == "spvar":
        model_path = MODELS_DIR / "spvar" / "spvar_model_lag3.pkl"
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    _models_cache[model_type] = model
    return model

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post(f"{config.api.api_prefix}/auth/register", response_model=TokenResponse, tags=["Authentication"])
async def register(user_data: UserRegistration):
    """Register new user"""
    success, result = auth_service.register(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(result)
        )

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in
    )

@app.post(f"{config.api.api_prefix}/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(credentials: UserLogin):
    """User login"""
    token = auth_service.login(credentials.username, credentials.password)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
        expires_in=token.expires_in
    )

@app.post(f"{config.api.api_prefix}/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    new_access_token = auth_service.refresh_token(refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=config.auth.access_token_expire_minutes * 60
    )

@app.get(f"{config.api.api_prefix}/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user.to_dict()

# ============================================================================
# FORECAST ENDPOINTS
# ============================================================================

@app.post(f"{config.api.api_prefix}/forecasts", response_model=List[ForecastResponse], tags=["Forecasts"])
async def generate_forecast(
    request: ForecastRequest,
    current_user: User = Depends(require_permission("view_forecasts"))
):
    """Generate forecast for specified segment"""
    try:
        # Load model
        model = load_model(request.model_type)

        # Load recent data for forecast input
        test_file = DATA_DIR / "processed" / "barge_rates_test.csv"
        df = pd.read_csv(test_file)

        # Get last observations for forecast
        rate_cols = [c for c in df.columns if '_rate' in c and 'segment' in c and not '_sa' in c]
        recent_data = df[rate_cols].tail(10).values

        # Generate forecast
        forecast = model.forecast(recent_data[-3:], steps=request.horizon)

        # Find segment index
        try:
            segment_idx = rate_cols.index(request.segment)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid segment: {request.segment}"
            )

        # Create response
        responses = []
        base_date = datetime.now()

        for i in range(request.horizon):
            responses.append(ForecastResponse(
                segment=request.segment,
                forecast_date=base_date + timedelta(weeks=i+1),
                horizon=i+1,
                model_type=request.model_type,
                forecasted_rate=float(forecast[i, segment_idx])
            ))

        return responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation failed: {str(e)}"
        )

@app.get(f"{config.api.api_prefix}/forecasts/historical", response_model=List[HistoricalData], tags=["Forecasts"])
async def get_historical_forecasts(
    segment: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    current_user: User = Depends(require_permission("view_forecasts"))
):
    """Get historical forecast data"""
    try:
        # Load forecast history
        forecast_file = BASE_DIR / "forecasting" / "results" / "forecasts" / "var_rolling_forecasts.csv"

        if not forecast_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Historical forecast data not found"
            )

        df = pd.read_csv(forecast_file)

        # Filter by segment
        actual_col = f"{segment}_actual"
        if actual_col not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid segment: {segment}"
            )

        # Create response (using period as proxy for date)
        results = []
        for idx, row in df.head(limit).iterrows():
            results.append(HistoricalData(
                segment=segment,
                date=datetime(2021, 1, 1) + timedelta(weeks=int(row['period'])),
                rate=float(row[actual_col])
            ))

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve historical data: {str(e)}"
        )

# ============================================================================
# MODEL ENDPOINTS
# ============================================================================

@app.get(f"{config.api.api_prefix}/models/performance", response_model=List[ModelPerformance], tags=["Models"])
async def get_model_performance(
    model_type: str = "var",
    current_user: User = Depends(require_permission("view_forecasts"))
):
    """Get model performance metrics"""
    try:
        # Load performance results
        results_file = BASE_DIR / "forecasting" / "results" / "forecast_accuracy_comparison.csv"

        if not results_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Performance data not found"
            )

        df = pd.read_csv(results_file)

        # Extract metrics
        responses = []
        for _, row in df.iterrows():
            if model_type == "var":
                responses.append(ModelPerformance(
                    model_type="var",
                    segment=row['segment'],
                    mae=float(row['var_mae']),
                    rmse=float(row['var_rmse']),
                    mape=float(row['var_mape']),
                    r_squared=float(row['var_r2'])
                ))
            elif model_type == "spvar":
                responses.append(ModelPerformance(
                    model_type="spvar",
                    segment=row['segment'],
                    mae=float(row['spvar_mae']),
                    rmse=float(row['spvar_rmse']),
                    mape=float(row['spvar_mape']),
                    r_squared=float(row['spvar_r2'])
                ))

        return responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )

@app.get(f"{config.api.api_prefix}/models/segments", tags=["Models"])
async def list_segments(
    current_user: User = Depends(require_permission("view_forecasts"))
):
    """List available river segments"""
    segments = [
        {"id": "segment_1_rate", "name": "Segment 1", "description": "Upper Mississippi"},
        {"id": "segment_2_rate", "name": "Segment 2", "description": "Mid-Upper Mississippi"},
        {"id": "segment_3_rate", "name": "Segment 3", "description": "Mid Mississippi"},
        {"id": "segment_4_rate", "name": "Segment 4", "description": "Lower Mid Mississippi"},
        {"id": "segment_5_rate", "name": "Segment 5", "description": "Upper Lower Mississippi"},
        {"id": "segment_6_rate", "name": "Segment 6", "description": "Mid Lower Mississippi"},
        {"id": "segment_7_rate", "name": "Segment 7", "description": "Lower Mississippi to Gulf"}
    ]

    return {"segments": segments, "count": len(segments)}

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get(f"{config.api.api_prefix}/admin/users", tags=["Admin"])
async def list_users(
    current_user: User = Depends(require_permission("manage_users"))
):
    """List all users (admin only)"""
    users = auth_service.user_manager.list_users()
    return {"users": [u.to_dict() for u in users], "count": len(users)}

@app.put(f"{config.api.api_prefix}/admin/users/{{username}}/role", tags=["Admin"])
async def update_user_role(
    username: str,
    new_role: str,
    current_user: User = Depends(require_permission("manage_users"))
):
    """Update user role (admin only)"""
    success, message = auth_service.user_manager.update_user_role(username, new_role)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {"message": message}

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get(f"{config.api.api_prefix}/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """API health check"""
    # Check if models can be loaded
    models_loaded = True
    try:
        load_model("var")
    except:
        models_loaded = False

    return HealthCheck(
        status="healthy" if models_loaded else "degraded",
        timestamp=datetime.now(),
        api_version=config.api.api_version,
        models_loaded=models_loaded
    )

@app.get(f"{config.api.api_prefix}/status", tags=["System"])
async def get_status():
    """Get API status and statistics"""
    return {
        "api_version": config.api.api_version,
        "environment": config.environment,
        "timestamp": datetime.now().isoformat(),
        "models": {
            "var": "loaded" if "var" in _models_cache else "not loaded",
            "spvar": "loaded" if "spvar" in _models_cache else "not loaded"
        },
        "uptime_seconds": 0  # Would need actual uptime tracking
    }

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Barge Rate Forecasting API",
        "version": config.api.api_version,
        "docs": f"{config.api.api_prefix}/docs",
        "health": f"{config.api.api_prefix}/health"
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("=" * 70)
    print("BARGE RATE FORECASTING API")
    print("=" * 70)
    print(f"Environment: {config.environment}")
    print(f"API Version: {config.api.api_version}")
    print(f"API Prefix: {config.api.api_prefix}")
    print(f"Docs: http://{config.api.host}:{config.api.port}{config.api.api_prefix}/docs")
    print("=" * 70)

    # Pre-load models
    try:
        load_model("var")
        print("✓ VAR model loaded")
    except Exception as e:
        print(f"✗ VAR model load failed: {e}")

    try:
        load_model("spvar")
        print("✓ SpVAR model loaded")
    except Exception as e:
        print(f"✗ SpVAR model load failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\nShutting down API...")
    _models_cache.clear()

# ============================================================================
# MAIN (FOR DEVELOPMENT)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
        workers=1 if config.api.debug else config.api.workers
    )
