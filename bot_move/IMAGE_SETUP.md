# Setting Up Map and Flag Images

The country guessing game requires access to map and flag images for all countries. This document explains how to set up these images in your project.

## Option 1: Using Local Image Files (Recommended)

This approach uses locally stored image files, which provides faster access and better reliability.

### Step 1: Download Image Zip Files
From the original project, download:
- `wiki_all_map_400pi.zip` (22MB) - Contains all country maps
- `wiki_flag.zip` (304KB) - Contains all country flags

### Step 2: Extract Files
Extract both zip files in your CryptoPriceBot project root, maintaining the folder structure:
```
CryptoPriceBot/
  ├── wiki_all_map_400pi/
  │   ├── Afghanistan_locator_map.png
  │   ├── Albania_locator_map.png
  │   └── ... (all country maps)
  └── wiki_flag/
      ├── Afghanistan_flag.png
      ├── Albania_flag.png
      └── ... (all country flags)
```

### Step 3: Verify File Paths
Make sure the code is referencing the correct paths. In `country_database.py` and `game_handler.py`, verify that the image paths are correct:

```python
# Typically looks like:
map_url = f"./wiki_all_map_400pi/{country_name}_locator_map.png"
flag_url = f"./wiki_flag/{country_name}_flag.png"
```

## Option 2: Using Remote URLs

If you prefer not to store images locally, you can modify the code to use remote URLs.

### Step 1: Modify Image URL Generation
Edit `country_database.py` to use remote URLs instead of local files:

```python
def get_map_url(self, country):
    country_name = country['name']['common']
    formatted_name = country_name.replace(" ", "_")
    
    # Use a remote URL pattern
    return f"https://example.com/maps/{formatted_name}_map.png"
```

### Step 2: Find Reliable Image Sources
Some reliable sources for country maps and flags:
- REST Countries API: https://restcountries.com/ (provides flag URLs)
- Wikimedia Commons: https://commons.wikimedia.org/
- FlagCDN: https://flagcdn.com/

## Option 3: Mixed Approach

You can also use a mixed approach:

1. Store the most commonly used country images locally
2. Fetch less common ones from remote URLs

To implement this:

```python
def get_map_url(self, country):
    country_name = country['name']['common']
    formatted_name = country_name.replace(" ", "_")
    local_path = f"./wiki_all_map_400pi/{formatted_name}_locator_map.png"
    
    # Check if local file exists
    import os
    if os.path.exists(local_path):
        return local_path
    
    # Fall back to remote URL
    return f"https://example.com/maps/{formatted_name}_map.png"
```

## Testing Your Image Setup

Run the following test to verify your image setup:

```python
from country_database import get_database
from game_handler import GameHandler

# Initialize components
db = get_database()
game = GameHandler()

# Test a specific country
test_country = db.get_country_by_name("United States")
map_url = db.get_map_url(test_country)
flag_url = game._get_flag_url(test_country)

print(f"Map URL: {map_url}")
print(f"Flag URL: {flag_url}")

# Verify files exist if using local paths
import os
if map_url.startswith("./"):
    print(f"Map file exists: {os.path.exists(map_url)}")
if flag_url.startswith("./"):
    print(f"Flag file exists: {os.path.exists(flag_url)}")
```

This will help you verify that your image setup is working correctly.