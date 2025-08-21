"""KV Store Service - A thread-safe in-memory key-value storage API.

Provides RESTful endpoints for storing, retrieving, updating, and deleting
key-value pairs with JSON serializable values.
"""
from fastapi import FastAPI, status
from models import ValueModel, KeyNotFoundError, KeyMismatchError, InternalServerError
import threading
import logging
import time
from typing import Dict, Any

app = FastAPI(title="KV Store Service", version="1.0.0")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("kv-service")

# Thread-safe in-memory storage
storage: Dict[str, Any] = {}
storage_lock = threading.RLock()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "healthy"}

@app.post("/keys/{key}", status_code=status.HTTP_201_CREATED)
async def store_key(key: str, data: ValueModel):
    """Store a new key-value pair."""
    start_time = time.time()
    logger.info(f"Storing key: {key}")
    
    try:
        if key != data.key:
            logger.warning(f"Key mismatch: path='{key}', body='{data.key}'")
            raise KeyMismatchError(key, data.key)
        
        with storage_lock:
            storage[key] = data.value
        
        duration = time.time() - start_time
        logger.info(f"Successfully stored key '{key}' in {duration:.3f}s")
        return {"success": True, "message": "Value stored successfully"}
        
    except KeyMismatchError:
        raise
    except Exception as e:
        logger.error(f"Error storing key '{key}': {e}")
        raise InternalServerError(f"Failed to store key: {str(e)}")

@app.put("/keys/{key}")
async def update_key(key: str, data: ValueModel):
    """Update an existing key-value pair."""
    start_time = time.time()
    logger.info(f"Updating key: {key}")
    
    try:
        if key != data.key:
            logger.warning(f"Key mismatch: path='{key}', body='{data.key}'")
            raise KeyMismatchError(key, data.key)
        
        with storage_lock:
            storage[key] = data.value
        
        duration = time.time() - start_time
        logger.info(f"Successfully updated key '{key}' in {duration:.3f}s")
        return {"success": True, "message": "Value stored successfully"}
        
    except KeyMismatchError:
        raise
    except Exception as e:
        logger.error(f"Error updating key '{key}': {e}")
        raise InternalServerError(f"Failed to update key: {str(e)}")

@app.get("/keys/{key}")
async def get_key(key: str):
    """Retrieve a value by key."""
    start_time = time.time()
    logger.info(f"Retrieving key: {key}")
    
    try:
        with storage_lock:
            if key not in storage:
                logger.warning(f"Key not found: {key}")
                raise KeyNotFoundError(key)
            
            value = storage[key]
        
        duration = time.time() - start_time
        logger.info(f"Successfully retrieved key '{key}' in {duration:.3f}s")
        return {"success": True, "key": key, "value": value}
        
    except KeyNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving key '{key}': {e}")
        raise InternalServerError(f"Failed to retrieve key: {str(e)}")

@app.delete("/keys/{key}")
async def delete_key(key: str):
    """Delete a key-value pair."""
    start_time = time.time()
    logger.info(f"Deleting key: {key}")
    
    try:
        with storage_lock:
            if key not in storage:
                logger.warning(f"Key not found for deletion: {key}")
                raise KeyNotFoundError(key)
            
            del storage[key]
        
        duration = time.time() - start_time
        logger.info(f"Successfully deleted key '{key}' in {duration:.3f}s")
        return {"success": True, "message": "Key deleted successfully"}
        
    except KeyNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting key '{key}': {e}")
        raise InternalServerError(f"Failed to delete key: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("KV Store Service starting up...")
    logger.info(f"Service version: {app.version}")
    
@app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown event handler."""
    with storage_lock:
        key_count = len(storage)
    logger.info(f"KV Store Service shutting down with {key_count} keys in storage")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting KV Store Service...")
    uvicorn.run(app, host="0.0.0.0", port=8000)