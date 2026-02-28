# Barge Rate Forecasting Dashboard

Interactive Streamlit dashboard for visualizing and analyzing Mississippi River barge freight rate forecasts.

## Features

- 📈 **Real-time Forecasts**: Interactive 1-week ahead predictions
- 📊 **Model Comparison**: VAR vs SpVAR performance visualization
- 🎯 **Accuracy Tracking**: MAE, RMSE, MAPE metrics
- 🔍 **Segment Drill-Down**: Focus on specific river segments
- 📅 **Date Range Filtering**: Analyze specific time periods
- 📉 **Error Analysis**: Forecast error distributions

## Quick Start

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Dashboard

1. Navigate to dashboard directory:
```bash
cd "G:\My Drive\LLM\project_barge\dashboard"
```

2. Launch Streamlit:
```bash
streamlit run app.py
```

3. Dashboard will open in your default browser at `http://localhost:8501`

### Alternative Launch (Windows)

Double-click the launcher script:
```bash
run_dashboard.bat
```

## Dashboard Tabs

### 1. 📈 Forecasts
- Interactive line chart of actual vs. forecasted rates
- Real-time metric cards (MAE, MAPE)
- Summary statistics for selected segment
- Date range filtering

### 2. 📊 Performance
- Accuracy comparison across all 7 river segments
- Side-by-side MAPE comparison (VAR vs SpVAR)
- Detailed performance metrics table
- Improvement percentage calculations

### 3. 🎯 Accuracy
- Forecast error distribution histogram
- Detailed accuracy metrics (VAR and SpVAR)
- Literature benchmark comparison
- Statistical test results summary

### 4. ℹ️ Info
- Model specifications and methodology
- Data sources and validation framework
- Usage tips and best practices
- System information

## Navigation

**Sidebar Controls:**
- **Model Selection**: Choose VAR, SpVAR, or Both
- **Segment Selection**: Select specific river segment
- **Date Range Slider**: Filter forecast periods

**Main Area:**
- **Tabs**: Switch between Forecasts, Performance, Accuracy, and Info views
- **Interactive Charts**: Hover for details, zoom, pan

## Data Requirements

Dashboard requires the following files in `forecasting/` directory:

**Data Files:**
- `data/processed/barge_rates_test.csv`

**Forecast Files:**
- `results/forecasts/var_rolling_forecasts.csv`
- `results/forecasts/spvar_comparison_forecasts.csv`

**Model Files:**
- `models/var/var_model_lag3.pkl`
- `models/spvar/spvar_model_lag3.pkl`

**Results Files:**
- `results/forecast_comparison_summary.json`

All files created by running forecasting scripts (01-05).

## Technical Specifications

**Framework:** Streamlit 1.28+
**Charts:** Plotly 5.17+
**Data:** Pandas 1.5+
**Models:** Scikit-learn 1.3+

**Browser Support:**
- Chrome 90+ (Recommended)
- Firefox 88+
- Edge 90+
- Safari 14+

## Features in Detail

### Real-time Forecasting
- Load pre-trained VAR/SpVAR models
- Display 1-5 week ahead forecasts
- Update based on selected segment/date range

### Interactive Visualization
- Plotly-based interactive charts
- Zoom, pan, hover tooltips
- Export charts as PNG
- Responsive layout

### Performance Metrics
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Percentage Error (MAPE)
- Mean Error (bias)
- R² correlation

### Model Comparison
- Side-by-side VAR vs SpVAR
- Statistical significance indicators
- Improvement percentages
- Segment-specific analysis

## Customization

### Adding New Segments

Edit `app.py` to modify segment handling:
```python
segment_names = get_segment_names(df_test)
```

### Changing Color Schemes

Modify Plotly color settings:
```python
line=dict(color='your_color', width=2)
```

### Adjusting Layout

Update Streamlit page config:
```python
st.set_page_config(
    page_title="Your Title",
    layout="wide"
)
```

## Troubleshooting

### Dashboard won't start
- Check Python version (3.8+required)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Ensure forecasting scripts have been run

### Data not loading
- Verify file paths in `app.py` BASE_DIR configuration
- Check all required CSV/JSON files exist
- Review file permissions

### Charts not rendering
- Update Plotly: `pip install --upgrade plotly`
- Clear browser cache
- Try different browser

### Performance issues
- Reduce date range filter
- Close other browser tabs
- Increase Python memory limit

## Deployment Options

### Local (Current)
- Run on local machine
- Access via localhost
- Development and testing

### Streamlit Cloud (Recommended for sharing)
1. Push code to GitHub
2. Connect Streamlit Cloud account
3. Deploy from repository
4. Share public URL

### Docker Container
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

### Enterprise Server
- Deploy on internal server
- Configure authentication
- Set up automated data updates
- Integrate with ERP/TMS systems

## Future Enhancements

### Planned Features
- [ ] Multi-step ahead forecast display (2-5 weeks)
- [ ] Scenario analysis tools (what-if)
- [ ] Confidence interval visualization
- [ ] Export to PDF/Excel reports
- [ ] Real-time data integration
- [ ] User authentication
- [ ] Alert system for rate anomalies
- [ ] Cost savings calculator
- [ ] Historical backtest viewer
- [ ] Mobile-responsive design

### Data Integration
- [ ] Connect to USDA AMS API
- [ ] Real-time USACE river gauge data
- [ ] EIA fuel price feeds
- [ ] Automated daily updates

### Analytics
- [ ] Forecast decomposition
- [ ] Feature importance analysis
- [ ] Regime detection (drought vs normal)
- [ ] Seasonal pattern breakdown

## API Documentation

### Loading Models

```python
import pickle

# Load VAR model
with open('models/var/var_model_lag3.pkl', 'rb') as f:
    var_model = pickle.load(f)

# Generate forecast
forecast = var_model.forecast(data[-3:], steps=5)
```

### Calculating Metrics

```python
def calculate_metrics(actual, forecast):
    errors = actual - forecast
    return {
        'MAE': np.mean(np.abs(errors)),
        'RMSE': np.sqrt(np.mean(errors**2)),
        'MAPE': np.mean(np.abs(errors / actual)) * 100
    }
```

## Support

**Documentation:**
- Technical Report: `../forecasting/FORECASTING_FINAL_REPORT.md`
- Methodology: `../forecasting/README.md`
- Session Log: `../SESSION_UPDATE_2026_02_03_CONTINUED.md`

**Resources:**
- Streamlit Docs: https://docs.streamlit.io
- Plotly Docs: https://plotly.com/python/
- VAR Models: statsmodels documentation

## License

Internal research project - Barge Economics Research Team

## Version History

**v1.0** (February 3, 2026)
- Initial dashboard release
- VAR and SpVAR forecast visualization
- 4-tab interface (Forecasts, Performance, Accuracy, Info)
- Interactive Plotly charts
- Segment and date filtering
- Performance metrics comparison

## Contributors

Barge Economics Research Team
- Econometric modeling
- Dashboard development
- Documentation

---

**Status:** Production Ready ✓
**Last Updated:** February 3, 2026
