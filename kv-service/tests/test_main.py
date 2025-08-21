import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
import threading

# Import the app and storage from main module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, storage, storage_lock
from models import ValueModel, KeyNotFoundError, KeyMismatchError, ValidationError, InternalServerError

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    with storage_lock:
        storage.clear()
    yield
    with storage_lock:
        storage.clear()

class TestHealthCheck:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestValueModel:
    def test_valid_json_values(self):
        """Test ValueModel with valid JSON serializable values"""
        # Test string
        model = ValueModel(key="test", value="hello")
        assert model.key == "test"
        assert model.value == "hello"
        
        # Test number
        model = ValueModel(key="test", value=42)
        assert model.value == 42
        
        # Test boolean
        model = ValueModel(key="test", value=True)
        assert model.value is True
        
        # Test null
        model = ValueModel(key="test", value=None)
        assert model.value is None
        
        # Test array
        model = ValueModel(key="test", value=[1, 2, "three"])
        assert model.value == [1, 2, "three"]
        
        # Test object
        model = ValueModel(key="test", value={"name": "John", "age": 30})
        assert model.value == {"name": "John", "age": 30}
    
    def test_invalid_json_values(self):
        """Test ValueModel with non-JSON serializable values"""
        # This should be handled by Pydantic validation
        with pytest.raises(ValueError):
            # Function is not JSON serializable
            ValueModel(key="test", value=lambda x: x)

class TestStoreKey:
    def test_store_key_success(self):
        """Test successful key storage"""
        response = client.post(
            "/keys/testkey",
            json={"key": "testkey", "value": "testvalue"}
        )
        assert response.status_code == 201
        assert response.json() == {"success": True, "message": "Value stored successfully"}
        
        # Verify storage
        with storage_lock:
            assert storage["testkey"] == "testvalue"
    
    def test_store_key_with_complex_value(self):
        """Test storing complex JSON values"""
        complex_value = {
            "string": "hello",
            "number": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"a": 1, "b": 2}
        }
        
        response = client.post(
            "/keys/complex",
            json={"key": "complex", "value": complex_value}
        )
        assert response.status_code == 201
        
        # Verify storage
        with storage_lock:
            assert storage["complex"] == complex_value
    
    def test_store_key_mismatch(self):
        """Test key mismatch between path and body"""
        response = client.post(
            "/keys/pathkey",
            json={"key": "bodykey", "value": "testvalue"}
        )
        assert response.status_code == 400
        assert response.json()["detail"]["success"] is False
        assert "does not match" in response.json()["detail"]["error"]
    
    def test_store_key_missing_fields(self):
        """Test missing required fields"""
        # Missing key field
        response = client.post(
            "/keys/testkey",
            json={"value": "testvalue"}
        )
        assert response.status_code == 422
        
        # Missing value field
        response = client.post(
            "/keys/testkey",
            json={"key": "testkey"}
        )
        assert response.status_code == 422
    
    def test_store_key_overwrite(self):
        """Test overwriting existing key"""
        # Store initial value
        response = client.post(
            "/keys/testkey",
            json={"key": "testkey", "value": "initial"}
        )
        assert response.status_code == 201
        
        # Overwrite with new value
        response = client.post(
            "/keys/testkey", 
            json={"key": "testkey", "value": "updated"}
        )
        assert response.status_code == 201
        
        # Verify updated value
        with storage_lock:
            assert storage["testkey"] == "updated"

class TestUpdateKey:
    def test_update_key_success(self):
        """Test successful key update"""
        # Store initial value
        with storage_lock:
            storage["testkey"] = "initial"
        
        response = client.put(
            "/keys/testkey",
            json={"key": "testkey", "value": "updated"}
        )
        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Value stored successfully"}
        
        # Verify storage
        with storage_lock:
            assert storage["testkey"] == "updated"
    
    def test_update_key_mismatch(self):
        """Test key mismatch in update"""
        response = client.put(
            "/keys/pathkey",
            json={"key": "bodykey", "value": "testvalue"}
        )
        assert response.status_code == 400
        assert response.json()["detail"]["success"] is False

class TestGetKey:
    def test_get_key_success(self):
        """Test successful key retrieval"""
        # Store test data
        test_value = {"name": "John", "age": 30}
        with storage_lock:
            storage["testkey"] = test_value
        
        response = client.get("/keys/testkey")
        assert response.status_code == 200
        
        expected_response = {
            "success": True,
            "key": "testkey", 
            "value": test_value
        }
        assert response.json() == expected_response
    
    def test_get_key_not_found(self):
        """Test retrieving non-existent key"""
        response = client.get("/keys/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"]["success"] is False
        assert "not found" in response.json()["detail"]["error"]
    
    def test_get_various_value_types(self):
        """Test retrieving different value types"""
        test_cases = [
            ("string_key", "hello world"),
            ("number_key", 42),
            ("float_key", 3.14),
            ("boolean_key", True),
            ("null_key", None),
            ("array_key", [1, 2, "three"]),
            ("object_key", {"a": 1, "b": [2, 3]})
        ]
        
        # Store test data
        with storage_lock:
            for key, value in test_cases:
                storage[key] = value
        
        # Test retrieval
        for key, expected_value in test_cases:
            response = client.get(f"/keys/{key}")
            assert response.status_code == 200
            assert response.json()["value"] == expected_value

class TestDeleteKey:
    def test_delete_key_success(self):
        """Test successful key deletion"""
        # Store test data
        with storage_lock:
            storage["testkey"] = "testvalue"
        
        response = client.delete("/keys/testkey")
        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Key deleted successfully"}
        
        # Verify deletion
        with storage_lock:
            assert "testkey" not in storage
    
    def test_delete_key_not_found(self):
        """Test deleting non-existent key"""
        response = client.delete("/keys/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"]["success"] is False
        assert "not found" in response.json()["detail"]["error"]

class TestConcurrentAccess:
    def test_concurrent_storage_operations(self):
        """Test thread-safe concurrent operations"""
        import threading
        import time
        
        def store_operation(key_prefix, count):
            for i in range(count):
                response = client.post(
                    f"/keys/{key_prefix}_{i}",
                    json={"key": f"{key_prefix}_{i}", "value": f"value_{i}"}
                )
                assert response.status_code == 201
        
        # Run concurrent storage operations
        thread1 = threading.Thread(target=store_operation, args=("thread1", 10))
        thread2 = threading.Thread(target=store_operation, args=("thread2", 10))
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # Verify all keys were stored
        with storage_lock:
            assert len(storage) == 20
            
            # Verify thread1 keys
            for i in range(10):
                assert storage[f"thread1_{i}"] == f"value_{i}"
            
            # Verify thread2 keys  
            for i in range(10):
                assert storage[f"thread2_{i}"] == f"value_{i}"

class TestErrorHandling:
    def test_internal_server_error_simulation(self):
        """Test internal server error handling"""
        # This is harder to test without mocking internal failures
        # For now, we can test that the error classes exist and work
        with pytest.raises(InternalServerError):
            raise InternalServerError("Test error")
    
    @patch('main.storage_lock')
    def test_storage_lock_exception(self, mock_lock):
        """Test exception handling when storage operations fail"""
        # Mock the lock to raise an exception
        mock_lock.__enter__.side_effect = Exception("Lock failure")
        
        response = client.post(
            "/keys/testkey",
            json={"key": "testkey", "value": "testvalue"}
        )
        # Should get 500 internal server error
        assert response.status_code == 500
        assert response.json()["detail"]["success"] is False

class TestCompleteWorkflow:
    def test_full_crud_workflow(self):
        """Test complete CRUD workflow"""
        key = "workflow_test"
        initial_value = "initial_value"
        updated_value = "updated_value"
        
        # 1. Store key
        response = client.post(
            f"/keys/{key}",
            json={"key": key, "value": initial_value}
        )
        assert response.status_code == 201
        
        # 2. Retrieve key
        response = client.get(f"/keys/{key}")
        assert response.status_code == 200
        assert response.json()["value"] == initial_value
        
        # 3. Update key
        response = client.put(
            f"/keys/{key}",
            json={"key": key, "value": updated_value}
        )
        assert response.status_code == 200
        
        # 4. Verify update
        response = client.get(f"/keys/{key}")
        assert response.status_code == 200
        assert response.json()["value"] == updated_value
        
        # 5. Delete key
        response = client.delete(f"/keys/{key}")
        assert response.status_code == 200
        
        # 6. Verify deletion
        response = client.get(f"/keys/{key}")
        assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])