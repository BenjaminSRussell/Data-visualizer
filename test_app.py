#!/usr/bin/env python3
"""
Comprehensive test script for Data Visualizer application.
Tests all components without requiring a database connection.
"""

import sys


def test_imports():
    """Test that all modules can be imported."""
    print('[1/6] Testing Module Imports...')
    try:
        from app import config, database, models, datasets, api, main
        print('  [OK] All modules imported successfully')
        return True
    except Exception as e:
        print(f'  [FAIL] Import failed: {e}')
        return False


def test_configuration():
    """Test configuration settings."""
    print('\n[2/6] Testing Configuration...')
    try:
        from app.config import settings
        assert settings.APP_NAME == 'Data Visualizer'
        assert settings.APP_VERSION == '2.0.0'
        assert settings.DEFAULT_PAGE_SIZE > 0
        print(f'  [OK] {settings.APP_NAME} v{settings.APP_VERSION}')
        print(f'  [OK] Page size: {settings.DEFAULT_PAGE_SIZE}')
        return True
    except Exception as e:
        print(f'  [FAIL] Configuration test failed: {e}')
        return False


def test_models():
    """Test SQLAlchemy models."""
    print('\n[3/6] Testing Database Models...')
    try:
        from app import models

        # Get all model classes
        model_classes = [
            (name, getattr(models, name))
            for name in dir(models)
            if hasattr(getattr(models, name), '__tablename__')
        ]

        assert len(model_classes) >= 8, 'Not enough models defined'

        print(f'  [OK] {len(model_classes)} ORM models defined:')
        for name, cls in sorted(model_classes):
            table = cls.__tablename__
            print(f'    - {name:20s} -> {table}')

        return True
    except Exception as e:
        print(f'  [FAIL] Models test failed: {e}')
        return False


def test_datasets():
    """Test dataset definitions."""
    print('\n[4/6] Testing Dataset Definitions...')
    try:
        from app.datasets import DATASETS, get_dataset, list_datasets

        assert len(DATASETS) == 9, f'Expected 9 datasets, got {len(DATASETS)}'

        # Test get_dataset function
        urls_dataset = get_dataset('urls')
        assert urls_dataset is not None, 'URLs dataset not found'

        # Test list_datasets function
        all_datasets = list_datasets()
        assert len(all_datasets) == 9, 'list_datasets returned wrong count'

        print(f'  [OK] {len(DATASETS)} datasets defined')

        # Check SQL queries
        queries_with_sql = sum(1 for ds in DATASETS.values() if ds.sql_query)
        simple_queries = len(DATASETS) - queries_with_sql

        print(f'  [OK] {queries_with_sql} custom SQL queries')
        print(f'  [OK] {simple_queries} simple SELECT queries')

        return True
    except Exception as e:
        print(f'  [FAIL] Datasets test failed: {e}')
        return False


def test_api():
    """Test API endpoints."""
    print('\n[5/6] Testing API Endpoints...')
    try:
        from app.api import router

        # Count routes
        routes = [r for r in router.routes if hasattr(r, 'path')]

        print(f'  [OK] {len(routes)} API endpoints defined:')
        for route in sorted(routes, key=lambda r: r.path):
            if hasattr(route, 'methods'):
                methods = ', '.join(sorted(route.methods))
                print(f'    {methods:6s} {route.path}')

        return True
    except Exception as e:
        print(f'  [FAIL] API test failed: {e}')
        return False


def test_application():
    """Test FastAPI application."""
    print('\n[6/6] Testing FastAPI Application...')
    try:
        from app.main import app

        assert app.title == 'Data Visualizer'
        assert app.version == '2.0.0'

        # Count all routes
        all_routes = [r for r in app.routes if hasattr(r, 'path')]
        api_routes = [r for r in all_routes if r.path.startswith('/api')]
        ui_routes = [r for r in all_routes if not r.path.startswith('/api')
                     and not r.path.startswith('/docs')
                     and not r.path.startswith('/openapi')
                     and not r.path.startswith('/redoc')]

        print(f'  [OK] App initialized: {app.title} v{app.version}')
        print(f'  [OK] Total routes: {len(all_routes)}')
        print(f'  [OK] API routes: {len(api_routes)}')
        print(f'  [OK] UI routes: {len(ui_routes)}')

        return True
    except Exception as e:
        print(f'  [FAIL] Application test failed: {e}')
        return False


def main():
    """Run all tests."""
    print('=' * 60)
    print('Data Visualizer - Comprehensive Test Suite')
    print('=' * 60)
    print()

    # Run all tests
    tests = [
        test_imports,
        test_configuration,
        test_models,
        test_datasets,
        test_api,
        test_application
    ]

    results = [test() for test in tests]

    # Summary
    print()
    print('=' * 60)
    passed = sum(results)
    total = len(results)

    if all(results):
        print(f'PASS All {total} Tests Passed!')
        print('=' * 60)
        print()
        print('Application is ready to run with PostgreSQL.')
        print()
        print('Next steps:')
        print('  1. Install dependencies: pip install -r requirements.txt')
        print('  2. Setup PostgreSQL:')
        print('     createdb data_visualizer')
        print('     psql data_visualizer < database/schema.sql')
        print('  3. Configure .env file with DATABASE_URL')
        print('  4. Run: ./start.sh')
        print('     or: uvicorn app.main:app --reload')
        print()
        return 0
    else:
        print(f'[FAIL] {passed}/{total} Tests Passed, {total - passed} Failed')
        print('=' * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
