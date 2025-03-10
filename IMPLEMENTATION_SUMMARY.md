# Implementation Summary: Fixing Multiple Responses Issue

## Problem

The API server was returning multiple different responses for a single request, causing UI flickering issues in client applications. When a client makes one request to `/api/game/new`, the server would sometimes respond with multiple different countries instead of a single consistent response.

Key symptoms:
- Different game IDs for the same request
- Different countries being returned in sequential responses
- UI flickering as different data was rendered

## Root Cause Analysis

The issue occurred because:

1. The game ID generation was based solely on timestamps, which could differ even for the same request
2. The randomization of country selection happened on each request handling
3. There was no mechanism to ensure consistency for retried or duplicate requests
4. Network conditions or server processing could result in the same request being processed multiple times

## Solution

We implemented a comprehensive solution with multiple layers of protection:

### 1. Client Request ID

Added support for a client-generated request ID that's passed as a query parameter:

```python
client_request_id = request.args.get("client_request_id", str(uuid.uuid4()))
```

### 2. Response Caching

Implemented a cache to store responses by client request ID:

```python
# Check if we already have a response for this client request ID
with lock_for_locks:
    if client_request_id in request_response_cache:
        logger.info(f"Using cached response for client request ID: {client_request_id}")
        return jsonify(request_response_cache[client_request_id])
```

### 3. Deterministic Game ID Generation

Changed game ID generation to be deterministic based on the client request ID:

```python
# Create a deterministic game ID based on the client request ID
game_id_seed = int(hashlib.md5(client_request_id.encode()).hexdigest(), 16) % 10**10
game_id = int(str(int(time.time()))[:6] + str(game_id_seed)[:4])  # timestamp + hash
```

### 4. Request Locking

Retained the existing request locking mechanism to prevent concurrent processing of identical requests:

```python
# Only process this request if we can acquire the lock
with lock_for_locks:
    if request_key in request_locks:
        # If we already have a lock for this URL, return a response indicating
        # that the request is already being processed
        logger.warning(f"Duplicate request detected for {request_key}")
        return jsonify({
            "error": "This request is already being processed",
            "status": "duplicate_request",
            "client_request_id": client_request_id
        }), 429
    else:
        # Create a new lock for this request
        request_locks[request_key] = threading.Lock()
```

### 5. Memory Management

Added cleanup logic to prevent memory leaks from the response cache:

```python
# Cleanup old cache entries if we have too many
if len(request_response_cache) > 1000:  # arbitrary limit
    oldest_keys = sorted(
        request_response_cache.keys(),
        key=lambda k: request_response_cache[k].get("timestamp", 0)
    )[:100]  # Remove oldest 100
    for key in oldest_keys:
        if key in request_response_cache:
            del request_response_cache[key]
```

## Client Implementation

The sample client was updated to generate and pass client request IDs:

```python
def get_new_game(mode="map", client_request_id=None):
    # Generate a client request ID if not provided
    if client_request_id is None:
        client_request_id = str(uuid.uuid4())
        
    params = {
        "mode": mode,
        "client_request_id": client_request_id
    }
    
    response = requests.get(
        f"{API_BASE_URL}/game/new", 
        params=params,
        headers=HEADERS
    )
    game_data = response.json()
    
    # Store the client request ID in the game data for future reference
    game_data["client_request_id"] = client_request_id
    
    return game_data
```

## Testing Results

The implementation was tested by:

1. Making multiple requests with the same client request ID
2. Verifying that identical responses were returned
3. Testing with a new client request ID to ensure different data was returned

Results confirmed that:
- Using the same client_request_id returned identical game data
- Using different client_request_ids returned different game data
- The implementation successfully prevented the UI flickering issue

## Recommendations for Client Applications

Client applications should:

1. Generate a unique client request ID for each new game request
2. Store this ID with the game data
3. Reuse the same ID when retrying a failed request
4. Generate a new ID when a completely new game is needed

This approach ensures consistent responses and prevents UI flickering while still allowing for new games to be generated when needed.