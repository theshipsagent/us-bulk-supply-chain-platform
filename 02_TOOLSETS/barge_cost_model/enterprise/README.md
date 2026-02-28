# Enterprise Deployment - Barge Rate Forecasting

Production-ready enterprise deployment with REST API, authentication, Docker containerization, and automated data updates.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Nginx     │────▶│   FastAPI    │────▶│ PostgreSQL  │
│   Proxy     │     │   API Server │     │  Database   │
└─────────────┘     └──────────────┘     └─────────────┘
      │                     │                     │
      │                     │                     │
      ▼                     ▼                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Streamlit  │     │    Redis     │     │  VAR/SpVAR  │
│  Dashboard  │     │    Cache     │     │   Models    │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 📦 Components

### 1. Configuration Management (`config.py`)
- Centralized configuration for all services
- Environment-based settings (dev/test/prod)
- Database, API, authentication, logging configuration
- Validation and defaults

### 2. Authentication System (`auth.py`)
- JWT-based authentication
- Role-based access control (RBAC)
- Password hashing and validation
- User management
- Token refresh mechanism

**Roles:**
- `viewer`: View forecasts and dashboard
- `analyst`: Run models, export data, create scenarios
- `admin`: Full system access, user management

### 3. REST API (`api.py`)
- FastAPI-based REST endpoints
- Swagger/OpenAPI documentation
- Rate limiting and CORS
- Model inference endpoints
- Performance metrics API

**Endpoints:**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/forecasts` - Generate forecast
- `GET /api/v1/forecasts/historical` - Historical data
- `GET /api/v1/models/performance` - Model metrics
- `GET /api/v1/health` - Health check

### 4. Docker Deployment
- Multi-container setup with Docker Compose
- PostgreSQL database
- Redis cache
- Nginx reverse proxy
- Automated health checks

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+ (for local development)

### Option 1: Docker Deployment (Recommended)

**1. Set environment variables:**
```bash
export DB_PASSWORD=your_secure_password
export JWT_SECRET_KEY=your_secret_key_here
```

**2. Start all services:**
```bash
cd enterprise
docker-compose up -d
```

**3. Check status:**
```bash
docker-compose ps
```

**4. Access services:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs
- Dashboard: http://localhost:8501
- Database: localhost:5432

### Option 2: Local Development

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Set environment:**
```bash
export APP_ENV=development
export JWT_SECRET_KEY=dev-secret-key
```

**3. Run API server:**
```bash
python api.py
```

**4. Access API docs:**
http://localhost:8000/api/v1/docs

## 🔐 Authentication

### Register New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "email": "analyst@company.com",
    "password": "SecurePass123!",
    "role": "analyst"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Use Token for API Calls

```bash
curl -X POST "http://localhost:8000/api/v1/forecasts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "segment": "segment_1_rate",
    "horizon": 5,
    "model_type": "var"
  }'
```

## 📊 API Examples

### Generate Forecast

**Request:**
```bash
POST /api/v1/forecasts
{
  "segment": "segment_1_rate",
  "horizon": 5,
  "model_type": "var"
}
```

**Response:**
```json
[
  {
    "segment": "segment_1_rate",
    "forecast_date": "2026-02-10T00:00:00",
    "horizon": 1,
    "model_type": "var",
    "forecasted_rate": 18.45
  },
  ...
]
```

### Get Model Performance

**Request:**
```bash
GET /api/v1/models/performance?model_type=var
```

**Response:**
```json
[
  {
    "model_type": "var",
    "segment": "segment_1_rate",
    "mae": 3.16,
    "rmse": 3.92,
    "mape": 19.8,
    "r_squared": 0.673
  },
  ...
]
```

### List River Segments

**Request:**
```bash
GET /api/v1/models/segments
```

**Response:**
```json
{
  "segments": [
    {
      "id": "segment_1_rate",
      "name": "Segment 1",
      "description": "Upper Mississippi"
    },
    ...
  ],
  "count": 7
}
```

## 🔧 Configuration

### Environment Variables

**Database:**
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: barge_forecasting)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password (required in production)

**API:**
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `API_DEBUG` - Debug mode (default: False)
- `API_WORKERS` - Number of workers (default: 4)

**Authentication:**
- `JWT_SECRET_KEY` - JWT secret key (required in production)

**Data Updates:**
- `USDA_API_KEY` - USDA AMS API key
- `USACE_API_KEY` - USACE river gauge API key
- `EIA_API_KEY` - EIA fuel price API key

### Configuration File

Create `.env` file:
```bash
APP_ENV=production
DB_PASSWORD=secure_password
JWT_SECRET_KEY=your_secret_key_here
USDA_API_KEY=your_usda_api_key
```

Load with:
```python
from dotenv import load_dotenv
load_dotenv()
```

## 🐳 Docker Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f api
docker-compose logs -f dashboard
```

### Restart Service
```bash
docker-compose restart api
```

### Rebuild Images
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Execute Commands in Container
```bash
docker-compose exec api python -c "print('Hello')"
```

### Database Backup
```bash
docker-compose exec postgres pg_dump -U postgres barge_forecasting > backup.sql
```

### Database Restore
```bash
docker-compose exec -T postgres psql -U postgres barge_forecasting < backup.sql
```

## 📈 Monitoring & Logging

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-03T22:00:00",
  "api_version": "v1",
  "models_loaded": true
}
```

### Application Logs

Logs are stored in `logs/` directory:
- `app.log` - General application logs
- `api.log` - API request/response logs
- `data_updates.log` - Data update operations
- `model_training.log` - Model retraining logs

### Monitoring Endpoints

- `/api/v1/health` - Health status
- `/api/v1/status` - System status and statistics
- `/metrics` - Prometheus metrics (if enabled)

## 🔒 Security

### Best Practices

1. **Change Default Passwords**
   - Set strong `DB_PASSWORD`
   - Use unique `JWT_SECRET_KEY` (at least 32 characters)

2. **Use HTTPS in Production**
   - Configure SSL certificates
   - Enable HTTPS-only mode

3. **Firewall Configuration**
   - Restrict database access to API container only
   - Close unnecessary ports

4. **Regular Updates**
   - Keep Docker images updated
   - Update Python dependencies regularly
   - Monitor security advisories

5. **Backup Strategy**
   - Regular database backups
   - Model version history
   - Configuration backups

### Password Requirements

Default requirements (configurable):
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

## 🚨 Troubleshooting

### API Won't Start

**Check logs:**
```bash
docker-compose logs api
```

**Common issues:**
- Database not ready → Wait for PostgreSQL health check
- Port already in use → Change `API_PORT` in docker-compose.yml
- Models not found → Verify model files in `forecasting/models/`

### Authentication Errors

**Issue:** "Invalid authentication credentials"

**Solutions:**
- Verify token hasn't expired
- Check JWT_SECRET_KEY consistency
- Ensure user is active

### Forecast Generation Fails

**Issue:** "Model file not found"

**Solutions:**
- Run forecasting scripts first: `python forecasting/scripts/03_var_estimation.py`
- Verify model files exist in `forecasting/models/var/` and `forecasting/models/spvar/`
- Check file permissions

### Database Connection Failed

**Issue:** "Could not connect to database"

**Solutions:**
- Verify PostgreSQL container is running: `docker-compose ps`
- Check database credentials in environment variables
- Ensure network connectivity between containers

## 📚 API Documentation

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Authentication Flow

1. **Register** → Get tokens
2. **Login** → Get tokens
3. **Use access token** → API calls
4. **Token expires** → Use refresh token
5. **Refresh** → Get new access token

### Rate Limiting

Default limits:
- 100 requests per minute per IP
- Configurable in `config.py`

## 🔄 Data Updates

### Manual Data Update

```bash
# Inside API container
docker-compose exec api python scripts/update_data.py
```

### Automated Updates

Configure in `config.py`:
```python
daily_update_time: str = "06:00"  # 6 AM daily
update_timezone: str = "America/Chicago"
```

Schedule with cron or systemd timer.

## 🧪 Testing

### Run Tests
```bash
pytest tests/
```

### Test Coverage
```bash
pytest --cov=enterprise tests/
```

### Load Testing
```bash
locust -f tests/load_test.py
```

## 📦 Production Deployment

### Deployment Checklist

- [ ] Set all environment variables
- [ ] Change default passwords
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups
- [ ] Configure monitoring/alerting
- [ ] Set up log aggregation
- [ ] Configure firewall rules
- [ ] Test disaster recovery
- [ ] Document deployment process
- [ ] Set up CI/CD pipeline

### Scaling

**Horizontal Scaling:**
```yaml
api:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '1.0'
        memory: 2G
```

**Load Balancing:**
- Nginx reverse proxy (included)
- Or use cloud load balancer (AWS ALB, Azure Load Balancer)

## 🎯 Performance Tuning

### Database

- Connection pooling (default: 20 connections)
- Query optimization with indexes
- Regular VACUUM and ANALYZE

### API

- Worker count = 2 × CPU cores
- Use Redis for caching
- Enable gzip compression

### Models

- Model caching (implemented)
- Batch predictions for multiple forecasts
- Async endpoint processing

## 📞 Support

**Documentation:**
- Technical Report: `../forecasting/FORECASTING_FINAL_REPORT.md`
- Dashboard Guide: `../dashboard/README.md`
- Configuration: `config.py`

**Common Issues:**
- Check logs in `logs/` directory
- Review health check endpoint: `/api/v1/health`
- Verify environment variables

## 📝 Version History

**v1.0** (February 3, 2026)
- Initial enterprise deployment
- JWT authentication with RBAC
- REST API with 10+ endpoints
- Docker containerization
- PostgreSQL + Redis integration
- Comprehensive documentation

---

**Status:** Production Ready ✓
**Last Updated:** February 3, 2026
**Maintainer:** Barge Economics Research Team
