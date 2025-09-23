#!/usr/bin/env python3
"""
Cache management utilities for the Saleor product loading script.
"""

import json
import os
from typing import Dict

CACHE_DIR = "cache"
CACHE_FILES = {
    "categories": "categories_cache.json",
    "collections": "collections_cache.json", 
    "product_types": "product_types_cache.json",
    "attributes": "attributes_cache.json",
    "attribute_values": "attribute_values_cache.json",
    "channels": "channels_cache.json",
    "tax_classes": "tax_classes_cache.json",
    "product_type_attributes": "product_type_attributes_cache.json"
}

def load_cache(cache_type: str) -> Dict:
    """Load cache from JSON file"""
    cache_file = os.path.join(CACHE_DIR, CACHE_FILES[cache_type])
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}

def get_cache_stats():
    """Get statistics about cache usage"""
    stats = {}
    for cache_type, cache_file in CACHE_FILES.items():
        file_path = os.path.join(CACHE_DIR, cache_file)
        if os.path.exists(file_path):
            cache = load_cache(cache_type)
            stats[cache_type] = len(cache)
        else:
            stats[cache_type] = 0
    return stats

def print_cache_stats():
    """Print cache statistics"""
    stats = get_cache_stats()
    print("\n=== CACHE STATISTICS ===")
    for cache_type, count in stats.items():
        print(f"{cache_type}: {count} entries")
    print("=======================\n")

def clear_cache(cache_type: str = None):
    """Clear cache files. If cache_type is None, clears all caches."""
    if cache_type:
        cache_file = os.path.join(CACHE_DIR, CACHE_FILES[cache_type])
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"Cleared cache: {cache_type}")
        else:
            print(f"Cache file not found: {cache_type}")
    else:
        for cache_file in CACHE_FILES.values():
            file_path = os.path.join(CACHE_DIR, cache_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        print("Cleared all caches")

def view_cache(cache_type: str):
    """View the contents of a specific cache"""
    if cache_type not in CACHE_FILES:
        print(f"Invalid cache type: {cache_type}")
        print(f"Available cache types: {list(CACHE_FILES.keys())}")
        return
    
    cache = load_cache(cache_type)
    print(f"\n=== {cache_type.upper()} CACHE CONTENTS ===")
    if not cache:
        print("Cache is empty")
    else:
        for key, value in cache.items():
            print(f"{key}: {value}")
    print("=" * 40)

def main():
    """Main function for cache management"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cache_utils.py <command> [cache_type]")
        print("Commands:")
        print("  stats - Show cache statistics")
        print("  clear [cache_type] - Clear all caches or specific cache")
        print("  view <cache_type> - View contents of specific cache")
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        print_cache_stats()
    elif command == "clear":
        cache_type = sys.argv[2] if len(sys.argv) > 2 else None
        clear_cache(cache_type)
    elif command == "view":
        if len(sys.argv) < 3:
            print("Please specify cache type to view")
            return
        cache_type = sys.argv[2]
        view_cache(cache_type)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
