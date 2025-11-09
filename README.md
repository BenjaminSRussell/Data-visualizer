# Data Visualizer 2.0

A lightweight, Superset-inspired data visualization platform for exploring and displaying data from PostgreSQL. This tool focuses purely on data visualization and exploration, without complex analysis or data manipulation.

## Overview

Data Visualizer 2.0 is a complete refactor focused on:
- **Display Only**: View and explore data, no data manipulation
- **PostgreSQL-backed**: All data stored in PostgreSQL
- **Simple & Fast**: Clean web UI for data exploration
- **Dataset-centric**: Pre-defined datasets for common queries
- **REST API**: Full API for programmatic access

## Architecture

The application follows Apache Superset's design principles:

```
┌─────────────────────────────────────────┐
│          Web UI (Templates)             │
│   Dashboard | Datasets | URLs | Patterns│
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         REST API (FastAPI)              │
│  /api/datasets | /api/urls | /api/stats │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        Dataset Layer (datasets.py)      │
│   Pre-defined queries and data sources  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Database Layer (SQLAlchemy)          │
│   Models, Sessions, Connection Pool     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          PostgreSQL Database            │
│  urls | classifications | patterns | ...│
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Setup Database

```bash
# Create PostgreSQL database
createdb data_visualizer

# Run schema
psql data_visualizer < database/schema.sql
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
nano .env
```

Example `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/data_visualizer
HOST=0.0.0.0
PORT=8000
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

### 5. Access the Application

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/health

## Features

### Web Interface

#### Dashboard (`/`)
- Database statistics overview
- Quick access to all features
- Available datasets list

#### Dataset Explorer (`/datasets-explorer`)
- Browse pre-defined datasets
- Paginated data display
- Export capabilities

#### URL Explorer (`/url-explorer`)
- Search and filter URLs
- View URL details
- Filter by domain, status code

#### Patterns View (`/patterns`)
- Discovered patterns visualization
- Filter by pattern type
- Frequency and confidence metrics

### Pre-defined Datasets

The application includes several built-in datasets:

| Dataset | Description |
|---------|-------------|
| **URLs** | All crawled URLs with metadata |
| **URLs by Domain** | Aggregated statistics per domain |
| **Classifications** | URL classifications with confidence |
| **Page Metadata** | Detailed page content metadata |
| **Patterns** | Discovered patterns in the data |
| **Crawl Sessions** | Crawl session tracking |
| **Domain Statistics** | Comprehensive domain analytics |
| **Content Types** | Content type distribution |
| **Status Codes** | HTTP status code distribution |

### REST API

#### Core Endpoints

```bash
# Get statistics
GET /api/stats

# List datasets
GET /api/datasets

# Query dataset
GET /api/datasets/{dataset_name}?limit=100&offset=0

# List URLs
GET /api/urls?limit=50&domain=example.com

# Get URL details
GET /api/urls/{url_id}

# List domains
GET /api/domains

# List patterns
GET /api/patterns?pattern_type=temporal

# List crawl sessions
GET /api/sessions
```

#### Example API Usage

```python
import requests

# Get statistics
response = requests.get('http://localhost:8000/api/stats')
stats = response.json()
print(f"Total URLs: {stats['total_urls']}")

# Query a dataset
response = requests.get('http://localhost:8000/api/datasets/urls_by_domain')
data = response.json()
print(f"Found {data['total_count']} domains")

# Filter URLs by domain
response = requests.get('http://localhost:8000/api/urls?domain=example.com')
urls = response.json()
```

## Project Structure

```
Data-visualizer/
├── app/                      # Main application code
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api.py               # REST API endpoints
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── datasets.py          # Dataset definitions
│   ├── config.py            # Configuration
│   ├── templates/           # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── datasets.html
│   │   ├── urls.html
│   │   └── patterns.html
│   └── static/              # Static files (CSS, JS)
├── database/
│   └── schema.sql           # PostgreSQL schema
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── README.md               # This file
```

## Database Schema

### Core Tables

- **urls**: Main URL storage with metadata
- **classifications**: URL category classifications
- **page_metadata**: Detailed page content information
- **patterns**: Discovered data patterns
- **crawl_sessions**: Crawl tracking and statistics

See `database/schema.sql` for complete schema definition.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/data_visualizer` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `False` |

### Pagination

- Default page size: 50 records
- Maximum page size: 1000 records
- Configurable in `app/config.py`

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations

If you need to modify the schema:

```bash
# Backup existing data
pg_dump data_visualizer > backup.sql

# Update schema.sql

# Apply changes
psql data_visualizer < database/schema.sql
```

## Differences from Original Version

This refactor simplifies the application significantly:

### Removed
- FAIL Complex analysis modules (statistical, network, semantic)
- FAIL ML/AI components (transformers, torch, mlx)
- FAIL Pattern recognition engines
- FAIL Data validation and normalization pipelines
- FAIL Background task processing (Celery, Redis)
- FAIL File-based output (JSON, Markdown reports)

### Added
- PASS Simple web-based UI
- PASS Clean REST API
- PASS Dataset-centric architecture
- PASS PostgreSQL-only data source
- PASS Focus on data display and exploration

## API Documentation

Full interactive API documentation is available at `/api/docs` when the server is running. This includes:

- Request/response schemas
- Example requests
- Try-it-out functionality
- Authentication details (if enabled)

## Performance

- Connection pooling: 10 connections + 20 overflow
- Pagination: Efficient offset-based pagination
- Indexes: Optimized for common queries
- Query caching: Can be added via Redis (future enhancement)

## Security Considerations

- Always use environment variables for credentials
- Never commit `.env` files to version control
- Use strong passwords for database access
- Consider adding authentication to the web UI for production
- Implement rate limiting for API endpoints in production

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check the application logs
# Connection errors will show on startup
```

### Port Already in Use

```bash
# Change port in .env or use different port
uvicorn app.main:app --port 8001
```

### Empty Database

```bash
# Ensure schema is loaded
psql data_visualizer < database/schema.sql

# Check if tables exist
psql data_visualizer -c "\dt"
```

## License

MIT License - See LICENSE file for details

## Contributing

This is a refactored version focusing on data visualization. Contributions welcome for:

- Additional visualization types
- New dataset definitions
- UI/UX improvements
- Performance optimizations
- Documentation improvements

## Support

For issues or questions, please open an issue on GitHub.
