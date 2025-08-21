import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from main import app
from models import TestDetails, TestResponse, TestErrorResponse


@pytest.fixture
def client():
    """Test client fixture for FastAPI app"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_check(self, client):
        """Test health endpoint returns correct status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestStatusEndpoint:
    """Test the status endpoint"""
    
    def test_status_endpoint(self, client):
        """Test status endpoint returns service information"""
        response = client.get("/test/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "kv_service_url" in data
        assert data["status"] == "Test client is running"


class TestResponseModels:
    """Test Pydantic response models"""
    
    def test_test_details_model(self):
        """Test TestDetails model validation"""
        details = TestDetails(steps_executed=4, all_assertions_passed=True)
        assert details.steps_executed == 4
        assert details.all_assertions_passed is True
        
    def test_test_response_model(self):
        """Test TestResponse model validation"""
        details = TestDetails(steps_executed=4, all_assertions_passed=True)
        response = TestResponse(
            success=True,
            test_name="test_deletion",
            details=details
        )
        assert response.success is True
        assert response.test_name == "test_deletion"
        assert response.details.steps_executed == 4
        
    def test_test_error_response_model(self):
        """Test TestErrorResponse model validation"""
        error_response = TestErrorResponse(
            success=False,
            test_name="test_deletion",
            error="Key not found",
            step="retrieve"
        )
        assert error_response.success is False
        assert error_response.test_name == "test_deletion"
        assert error_response.error == "Key not found"
        assert error_response.step == "retrieve"


class TestDeletionWorkflow:
    """Test the deletion test workflow"""
    
    @patch('main.httpx.AsyncClient')
    def test_deletion_success(self, mock_client_class, client):
        """Test successful deletion workflow"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create proper mock responses
        store_response = MagicMock()
        store_response.status_code = 201
        
        get_response = MagicMock()
        get_response.status_code = 200
        get_response.json.return_value = {"value": "test_delete_value"}
        
        delete_response = MagicMock()
        delete_response.status_code = 200
        
        verify_response = MagicMock()
        verify_response.status_code = 404
        
        mock_client.post = AsyncMock(return_value=store_response)
        mock_client.get = AsyncMock(side_effect=[get_response, verify_response])
        mock_client.delete = AsyncMock(return_value=delete_response)
        
        response = client.post("/test/deletion")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["test_name"] == "test_deletion"
        assert data["details"]["steps_executed"] == 4
        assert data["details"]["all_assertions_passed"] is True
    
    @patch('main.httpx.AsyncClient')
    def test_deletion_store_failure(self, mock_client_class, client):
        """Test deletion workflow with store failure"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        store_response = MagicMock()
        store_response.status_code = 400
        store_response.text = "Bad request"
        
        mock_client.post = AsyncMock(return_value=store_response)
        
        response = client.post("/test/deletion")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_deletion"
        assert data["step"] == "store"
        assert data["error"] == "Bad request"
    
    @patch('main.httpx.AsyncClient')
    def test_deletion_retrieve_failure(self, mock_client_class, client):
        """Test deletion workflow with retrieve failure"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        store_response = MagicMock()
        store_response.status_code = 201
        
        get_response = MagicMock()
        get_response.status_code = 404
        get_response.text = "Key not found"
        
        mock_client.post = AsyncMock(return_value=store_response)
        mock_client.get = AsyncMock(return_value=get_response)
        
        response = client.post("/test/deletion")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_deletion"
        assert data["step"] == "retrieve"
        assert data["error"] == "Key not found"
    
    @patch('main.httpx.AsyncClient')
    def test_deletion_value_mismatch(self, mock_client_class, client):
        """Test deletion workflow with value mismatch"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        store_response = MagicMock()
        store_response.status_code = 201
        
        get_response = MagicMock()
        get_response.status_code = 200
        get_response.json.return_value = {"value": "wrong_value"}
        
        mock_client.post = AsyncMock(return_value=store_response)
        mock_client.get = AsyncMock(return_value=get_response)
        
        response = client.post("/test/deletion")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_deletion"
        assert data["step"] == "retrieve"
        assert data["error"] == "Value mismatch"
    
    @patch('main.httpx.AsyncClient')
    def test_deletion_timeout(self, mock_client_class, client):
        """Test deletion workflow with timeout"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        
        response = client.post("/test/deletion")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_deletion"
        assert data["step"] == "connection"
        assert data["error"] == "Timeout connecting to KV service"


class TestOverwriteWorkflow:
    """Test the overwrite test workflow"""
    
    @patch('main.httpx.AsyncClient')
    def test_overwrite_success(self, mock_client_class, client):
        """Test successful overwrite workflow"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock successful responses for each step
        store_response = MagicMock()
        store_response.status_code = 201
        
        get_original_response = MagicMock()
        get_original_response.status_code = 200
        get_original_response.json.return_value = {"value": "original_value"}
        
        overwrite_response = MagicMock()
        overwrite_response.status_code = 200
        
        get_new_response = MagicMock()
        get_new_response.status_code = 200
        get_new_response.json.return_value = {"value": "new_value"}
        
        delete_response = MagicMock()
        delete_response.status_code = 200
        
        mock_client.post = AsyncMock(return_value=store_response)
        mock_client.get = AsyncMock(side_effect=[get_original_response, get_new_response])
        mock_client.put = AsyncMock(return_value=overwrite_response)
        mock_client.delete = AsyncMock(return_value=delete_response)
        
        response = client.post("/test/overwrite")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["test_name"] == "test_overwrite"
        assert data["details"]["steps_executed"] == 4
        assert data["details"]["all_assertions_passed"] is True
    
    @patch('main.httpx.AsyncClient')
    def test_overwrite_store_failure(self, mock_client_class, client):
        """Test overwrite workflow with initial store failure"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        store_response = MagicMock()
        store_response.status_code = 400
        store_response.text = "Bad request"
        
        mock_client.post = AsyncMock(return_value=store_response)
        
        response = client.post("/test/overwrite")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_overwrite"
        assert data["step"] == "store_original"
        assert data["error"] == "Bad request"
    
    @patch('main.httpx.AsyncClient')
    def test_overwrite_put_failure(self, mock_client_class, client):
        """Test overwrite workflow with PUT operation failure"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        store_response = MagicMock()
        store_response.status_code = 201
        
        get_response = MagicMock()
        get_response.status_code = 200
        get_response.json.return_value = {"value": "original_value"}
        
        overwrite_response = MagicMock()
        overwrite_response.status_code = 500
        overwrite_response.text = "Internal server error"
        
        mock_client.post = AsyncMock(return_value=store_response)
        mock_client.get = AsyncMock(return_value=get_response)
        mock_client.put = AsyncMock(return_value=overwrite_response)
        
        response = client.post("/test/overwrite")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_overwrite"
        assert data["step"] == "overwrite"
        assert data["error"] == "Internal server error"
    
    @patch('main.httpx.AsyncClient')
    def test_overwrite_verify_failure(self, mock_client_class, client):
        """Test overwrite workflow with verification failure"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        store_response = MagicMock()
        store_response.status_code = 201
        
        get_original_response = MagicMock()
        get_original_response.status_code = 200
        get_original_response.json.return_value = {"value": "original_value"}
        
        overwrite_response = MagicMock()
        overwrite_response.status_code = 200
        
        get_new_response = MagicMock()
        get_new_response.status_code = 200
        get_new_response.json.return_value = {"value": "wrong_value"}
        
        mock_client.post = AsyncMock(return_value=store_response)
        mock_client.get = AsyncMock(side_effect=[get_original_response, get_new_response])
        mock_client.put = AsyncMock(return_value=overwrite_response)
        
        response = client.post("/test/overwrite")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_overwrite"
        assert data["step"] == "verify_new"
        assert data["error"] == "New value mismatch"


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('main.httpx.AsyncClient')
    def test_deletion_unexpected_error(self, mock_client_class, client):
        """Test deletion workflow with unexpected exception"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Unexpected error")
        
        response = client.post("/test/deletion")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_deletion"
        assert data["step"] == "unknown"
        assert "Unexpected error" in data["error"]
    
    @patch('main.httpx.AsyncClient')
    def test_overwrite_unexpected_error(self, mock_client_class, client):
        """Test overwrite workflow with unexpected exception"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Unexpected error")
        
        response = client.post("/test/overwrite")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["test_name"] == "test_overwrite"
        assert data["step"] == "unknown"
        assert "Unexpected error" in data["error"]


class TestApplicationLifecycle:
    """Test application startup and shutdown events"""
    
    def test_startup_event_coverage(self, client):
        """Test that startup events are properly configured"""
        # This test ensures the startup event handlers are defined
        # The actual testing of startup/shutdown requires more complex setup
        assert hasattr(app, 'router')
        
        # Verify the app has the expected routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/test/status", "/test/deletion", "/test/overwrite"]
        for expected_route in expected_routes:
            assert expected_route in routes