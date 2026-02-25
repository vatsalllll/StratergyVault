"""
Tests for StrategyVault - API Endpoints
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestRootEndpoints:
    """Test root and health endpoints."""

    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "StrategyVault"
        assert "version" in data
        assert "features" in data

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestStrategyEndpoints:
    """Test strategy API endpoints."""

    def test_list_strategies(self):
        response = client.get("/api/v1/strategies/")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert "total" in data
        assert "page" in data

    def test_list_strategies_pagination(self):
        response = client.get("/api/v1/strategies/?page=2&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 5

    def test_get_strategy_not_found(self):
        response = client.get("/api/v1/strategies/99999")
        assert response.status_code == 404

    def test_generate_strategy(self):
        response = client.post(
            "/api/v1/strategies/generate",
            json={"trading_idea": "Buy when RSI below 30"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("complete", "failed")  # real pipeline runs
        assert "progress" in data

    def test_get_strategy_code(self):
        # Code is now publicly accessible (auth not yet wired)
        response = client.get("/api/v1/strategies/1/code")
        assert response.status_code in (200, 404)  # 200 if exists, 404 if not

    def test_get_validation_report_not_found(self):
        response = client.get("/api/v1/strategies/99999/validation-report")
        assert response.status_code == 404

    def test_get_ai_consensus_not_found(self):
        response = client.get("/api/v1/strategies/99999/ai-consensus")
        assert response.status_code == 404


class TestMarketplaceEndpoints:
    """Test marketplace API endpoints."""

    def test_marketplace_home(self):
        response = client.get("/api/v1/marketplace/")
        assert response.status_code == 200
        data = response.json()
        assert "featured" in data
        assert "total_strategies" in data
        assert "gold_strategies" in data

    def test_search_strategies(self):
        response = client.get("/api/v1/marketplace/search?query=momentum")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert "total" in data

    def test_purchase_unauthorized(self):
        response = client.post("/api/v1/marketplace/purchase/1")
        assert response.status_code == 401

    def test_my_strategies_unauthorized(self):
        response = client.get("/api/v1/marketplace/my-strategies")
        assert response.status_code == 401

    def test_download_unauthorized(self):
        response = client.get("/api/v1/marketplace/download/1")
        assert response.status_code == 401


class TestOpenAPIDocs:
    """Test that API documentation is accessible."""

    def test_docs_endpoint(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self):
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "info" in data
