"""KV Store Test Client - Validation service for testing KV Store functionality.

Provides automated test endpoints for validating deletion and overwrite workflows
of the KV Store Service.
"""
from fastapi import FastAPI
from models import TestDetails, TestResponse, TestErrorResponse
import httpx
import os
import logging
import time

app = FastAPI(title="KV Store Test Client", version="1.0.0")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-client")

# Get KV service URL from environment
KV_SERVICE_URL = os.getenv("KV_SERVICE_URL", "http://kv-service:8000")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "healthy"}

@app.get("/test/status")
async def test_status():
    """Get test client status and configuration."""
    logger.info("Test status requested")
    return {"status": "Test client is running", "kv_service_url": KV_SERVICE_URL}

@app.post("/test/deletion")
async def test_deletion():
    """Test complete deletion workflow: store → retrieve → delete → verify deleted."""
    start_time = time.time()
    logger.info("Starting deletion test")
    
    test_key = "test_delete_key"
    test_value = "test_delete_value"
    steps_executed = 0
    
    async with httpx.AsyncClient() as client:
        try:
            # Store a key (Step 1)
            store_response = await client.post(
                f"{KV_SERVICE_URL}/keys/{test_key}",
                json={"key": test_key, "value": test_value},
                timeout=10.0
            )
            steps_executed += 1
            if store_response.status_code not in [200, 201]:
                return TestErrorResponse(
                    success=False,
                    test_name="test_deletion",
                    step="store",
                    error=store_response.text
                ).model_dump()
            
            # Retrieve the key (Step 2)
            get_response = await client.get(f"{KV_SERVICE_URL}/keys/{test_key}", timeout=10.0)
            steps_executed += 1
            if get_response.status_code != 200:
                return TestErrorResponse(
                    success=False,
                    test_name="test_deletion",
                    step="retrieve",
                    error=get_response.text
                ).model_dump()
            
            retrieved_data = get_response.json()
            if retrieved_data.get("value") != test_value:
                return TestErrorResponse(
                    success=False,
                    test_name="test_deletion",
                    step="retrieve",
                    error="Value mismatch"
                ).model_dump()
            
            # Delete the key (Step 3)
            delete_response = await client.delete(f"{KV_SERVICE_URL}/keys/{test_key}", timeout=10.0)
            steps_executed += 1
            if delete_response.status_code != 200:
                return TestErrorResponse(
                    success=False,
                    test_name="test_deletion",
                    step="delete",
                    error=delete_response.text
                ).model_dump()
            
            # Verify deletion (Step 4)
            verify_response = await client.get(f"{KV_SERVICE_URL}/keys/{test_key}", timeout=10.0)
            steps_executed += 1
            if verify_response.status_code != 404:
                return TestErrorResponse(
                    success=False,
                    test_name="test_deletion",
                    step="verify_deletion",
                    error="Key still exists"
                ).model_dump()
            
            duration = time.time() - start_time
            logger.info(f"Deletion test completed successfully in {duration:.3f}s")
            return TestResponse(
                success=True,
                test_name="test_deletion",
                details=TestDetails(
                    steps_executed=steps_executed,
                    all_assertions_passed=True
                )
            ).model_dump()
            
        except httpx.TimeoutException:
            logger.error("Deletion test failed: timeout connecting to KV service")
            return TestErrorResponse(
                success=False,
                test_name="test_deletion",
                step="connection",
                error="Timeout connecting to KV service"
            ).model_dump()
        except Exception as e:
            logger.error(f"Deletion test failed with unexpected error: {e}")
            return TestErrorResponse(
                success=False,
                test_name="test_deletion",
                step="unknown",
                error=str(e)
            ).model_dump()

@app.post("/test/overwrite")
async def test_overwrite():
    """Test complete overwrite workflow: store → retrieve → overwrite → verify new value."""
    start_time = time.time()
    logger.info("Starting overwrite test")
    
    test_key = "test_overwrite_key"
    original_value = "original_value"
    new_value = "new_value"
    steps_executed = 0
    
    async with httpx.AsyncClient() as client:
        try:
            # Store original value (Step 1)
            store_response = await client.post(
                f"{KV_SERVICE_URL}/keys/{test_key}",
                json={"key": test_key, "value": original_value},
                timeout=10.0
            )
            steps_executed += 1
            if store_response.status_code not in [200, 201]:
                return TestErrorResponse(
                    success=False,
                    test_name="test_overwrite",
                    step="store_original",
                    error=store_response.text
                ).model_dump()
            
            # Retrieve and verify original value (Step 2)
            get_response = await client.get(f"{KV_SERVICE_URL}/keys/{test_key}", timeout=10.0)
            steps_executed += 1
            if get_response.status_code != 200:
                return TestErrorResponse(
                    success=False,
                    test_name="test_overwrite",
                    step="retrieve_original",
                    error=get_response.text
                ).model_dump()
            
            retrieved_data = get_response.json()
            if retrieved_data.get("value") != original_value:
                return TestErrorResponse(
                    success=False,
                    test_name="test_overwrite",
                    step="retrieve_original",
                    error="Original value mismatch"
                ).model_dump()
            
            # Overwrite with new value (Step 3)
            overwrite_response = await client.put(
                f"{KV_SERVICE_URL}/keys/{test_key}",
                json={"key": test_key, "value": new_value},
                timeout=10.0
            )
            steps_executed += 1
            if overwrite_response.status_code != 200:
                return TestErrorResponse(
                    success=False,
                    test_name="test_overwrite",
                    step="overwrite",
                    error=overwrite_response.text
                ).model_dump()
            
            # Verify new value (Step 4)
            verify_response = await client.get(f"{KV_SERVICE_URL}/keys/{test_key}", timeout=10.0)
            steps_executed += 1
            if verify_response.status_code != 200:
                return TestErrorResponse(
                    success=False,
                    test_name="test_overwrite",
                    step="verify_new",
                    error=verify_response.text
                ).model_dump()
            
            verified_data = verify_response.json()
            if verified_data.get("value") != new_value:
                return TestErrorResponse(
                    success=False,
                    test_name="test_overwrite",
                    step="verify_new",
                    error="New value mismatch"
                ).model_dump()
            
            # Clean up
            await client.delete(f"{KV_SERVICE_URL}/keys/{test_key}", timeout=10.0)
            
            duration = time.time() - start_time
            logger.info(f"Overwrite test completed successfully in {duration:.3f}s")
            return TestResponse(
                success=True,
                test_name="test_overwrite",
                details=TestDetails(
                    steps_executed=steps_executed,
                    all_assertions_passed=True
                )
            ).model_dump()
            
        except httpx.TimeoutException:
            logger.error("Overwrite test failed: timeout connecting to KV service")
            return TestErrorResponse(
                success=False,
                test_name="test_overwrite",
                step="connection",
                error="Timeout connecting to KV service"
            ).model_dump()
        except Exception as e:
            logger.error(f"Overwrite test failed with unexpected error: {e}")
            return TestErrorResponse(
                success=False,
                test_name="test_overwrite",
                step="unknown",
                error=str(e)
            ).model_dump()

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Test Client starting up...")
    logger.info(f"KV Service URL: {KV_SERVICE_URL}")
    
@app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Test Client shutting down...")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Test Client...")
    uvicorn.run(app, host="0.0.0.0", port=8001)