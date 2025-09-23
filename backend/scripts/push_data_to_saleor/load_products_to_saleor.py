import csv
import json
import os
import re
import time
import requests
import tempfile
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load variables from .env into environment
load_dotenv()

# ========= CONFIG =========
# SALEOR_GQL_ENDPOINT = os.getenv("SALEOR_GQL_ENDPOINT", "https://your-saleor.com/graphql/")
SALEOR_GQL_ENDPOINT = os.getenv("SALEOR_ENDPOINT", "https://your-saleor.com/graphql/")
SALEOR_TOKEN = os.getenv("SALEOR_TOKEN", "REPLACE_ME")
CHANNEL_SLUG = os.getenv("CHANNEL_SLUG", "default-channel")

# Processing configuration
START_ROW = int(os.getenv("START_ROW", "1"))  # Start from this row (1-based, includes header)
TOTAL_RECORDS = int(os.getenv("TOTAL_RECORDS", "0"))  # Total records to process (0 = all records)
SKIP_HEADER = os.getenv("SKIP_HEADER", "true").lower() == "true"  # Whether to skip header row

# ========= CACHING SYSTEM =========
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

def ensure_cache_dir():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def load_cache(cache_type: str) -> Dict:
    """Load cache from JSON file"""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, CACHE_FILES[cache_type])
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}

def save_cache(cache_type: str, data: Dict):
    """Save cache to JSON file"""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, CACHE_FILES[cache_type])
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)

def get_cached_id(cache_type: str, key: str) -> Optional[str]:
    """Get cached ID for a given key"""
    cache = load_cache(cache_type)
    return cache.get(key)

def set_cached_id(cache_type: str, key: str, id_value: str):
    """Set cached ID for a given key"""
    cache = load_cache(cache_type)
    cache[key] = id_value
    save_cache(cache_type, cache)

# Initialize caches
ensure_cache_dir()

def load_image_mapping() -> Dict[str, str]:
    """Load the image mapping from JSON file"""
    mapping_file = "./images/images_and_mapping/mapping.json"
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading image mapping: {e}")
    return {}

def get_content_type_from_filename(filename: str) -> str:
    """Get content type from filename extension"""
    filename_lower = filename.lower()
    if filename_lower.endswith('.png'):
        return 'image/png'
    elif filename_lower.endswith('.jpg') or filename_lower.endswith('.jpeg'):
        return 'image/jpeg'
    elif filename_lower.endswith('.gif'):
        return 'image/gif'
    elif filename_lower.endswith('.webp'):
        return 'image/webp'
    else:
        return 'image/jpeg'  # Default

def clear_cache(cache_type: str = None):
    """Clear cache files. If cache_type is None, clears all caches."""
    if cache_type:
        cache_file = os.path.join(CACHE_DIR, CACHE_FILES[cache_type])
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"Cleared cache: {cache_type}")
    else:
        for cache_file in CACHE_FILES.values():
            file_path = os.path.join(CACHE_DIR, cache_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        print("Cleared all caches")

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

# ========= IMPROVED GQL FUNCTION =========
# def gql(query: str, variables: dict = None) -> dict:
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {SALEOR_TOKEN}",
#     }
#     payload = {"query": query, "variables": variables or {}}
    
#     print(f"Making request to: {SALEOR_GQL_ENDPOINT}")
#     print(f"Query: {query[:100]}...")
#     print(f"Variables: {json.dumps(variables, indent=2) if variables else 'None'}")
    
#     r = requests.post(SALEOR_GQL_ENDPOINT, headers=headers, json=payload)
    
#     print(f"Response status: {r.status_code}")
    
#     # Capture the actual error details before raising
#     if r.status_code != 200:
#         print(f"HTTP Error {r.status_code}: {r.text}")
#         try:
#             error_data = r.json()
#             print(f"Error details: {json.dumps(error_data, indent=2)}")
#         except:
#             pass
#         r.raise_for_status()
    
#     data = r.json()
#     if "errors" in data:
#         print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
#         raise RuntimeError(f"GraphQL errors: {data['errors']}")
#     return data["data"]

def gql(query: str, variables: dict = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SALEOR_TOKEN}",
    }
    payload = {"query": query, "variables": variables or {}}

    max_attempts = 6
    backoff = 1.0  # seconds
    for attempt in range(1, max_attempts + 1):
        print(f"Making request to: {SALEOR_GQL_ENDPOINT}")
        print(f"Query: {query[:100]}.")
        print(f"Variables: {json.dumps(variables, indent=2) if variables else 'None'}")

        r = requests.post(SALEOR_GQL_ENDPOINT, headers=headers, json=payload)
        print(f"Response status: {r.status_code}")

        # Happy path
        if r.status_code == 200:
            data = r.json()
            if "errors" in data:
                print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
                raise RuntimeError(f"GraphQL errors: {data['errors']}")
            return data["data"]

        # Handle throttling
        if r.status_code == 429:
            retry_after = 0.0
            try:
                retry_after = float(r.headers.get("Retry-After", "0"))
            except Exception:
                pass
            sleep_for = max(backoff, retry_after)
            print(f"429 Too Many Requests. Sleeping {sleep_for:.1f}s (attempt {attempt}/{max_attempts})")
            time.sleep(sleep_for)
            backoff = min(backoff * 2, 30)  # cap growth
            continue

        # Other HTTP errors: log details, then retry a few times with backoff
        print(f"HTTP Error {r.status_code}: {r.text}")
        if attempt < max_attempts:
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue
        # final attempt -> raise
        try:
            error_data = r.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            pass
        r.raise_for_status()


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")

def parse_decimal(cell) -> Optional[float]:
    """Parse numbers that may include commas, currency symbols, or be blank."""
    if cell is None:
        return None
    s = str(cell).strip()
    if not s:
        return None
    # remove currency symbols and spaces, drop thousand separators
    s = s.replace(",", "")
    s = re.sub(r"[^\d\.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


# ========= IMPROVED PRODUCT TYPE CREATION =========

# Updated mutation with direct fields (works with this Saleor instance)
M_PRODUCT_TYPE_CREATE_FIXED = """
mutation ($name: String!, $slug: String!, $hasVariants: Boolean!, $isDigital: Boolean, $isShippingRequired: Boolean) {
  productTypeCreate(input: { 
    name: $name, 
    slug: $slug, 
    hasVariants: $hasVariants,
    isDigital: $isDigital,
    isShippingRequired: $isShippingRequired
  }) {
    productType { 
      id 
      name 
      slug 
      hasVariants
      isDigital
      isShippingRequired
    }
    errors { 
      field 
      code 
      message 
    }
  }
}
"""

def get_or_create_product_type_fixed(slug: str, name: Optional[str] = None, has_variants: bool = True) -> str:
    """Improved product type creation with better error handling"""
    
    # Check cache first
    cached_id = get_cached_id("product_types", slug)
    if cached_id:
        print(f"Using cached product type: {slug} -> {cached_id}")
        return cached_id
    
    # First, try to find existing product type
    res = gql(Q_PRODUCT_TYPE_BY_SLUG, {"slug": slug})
    node = _pick_product_type_by_slug(res["productTypes"]["edges"], slug)
    if node:
        product_type_id = node["id"]
        set_cached_id("product_types", slug, product_type_id)
        print(f"Found and cached existing product type: {node['name']} ({product_type_id})")
        return product_type_id
    
    # Create new product type with all required fields
    name = name or slug.replace("-", " ").title()
    
    # Try different combinations of required fields
    input_variations = [
        # Basic required fields with all optional fields
        {
            "name": name,
            "slug": slug,
            "hasVariants": has_variants,
            "isDigital": False,
            "isShippingRequired": True
        },
        # Minimal required fields (only the essentials)
        {
            "name": name,
            "slug": slug,
            "hasVariants": has_variants
        }
    ]
    
    for i, input_data in enumerate(input_variations):
        try:
            print(f"Attempting product type creation (attempt {i+1}): {json.dumps(input_data, indent=2)}")
            create = gql(M_PRODUCT_TYPE_CREATE_FIXED, input_data)
            errs = create["productTypeCreate"]["errors"]
            if errs:
                print(f"Product type creation errors (attempt {i+1}): {errs}")
                continue
            product_type = create["productTypeCreate"]["productType"]
            product_type_id = product_type["id"]
            set_cached_id("product_types", slug, product_type_id)
            print(f"Successfully created and cached product type: {product_type['name']} ({product_type_id})")
            return product_type_id
        except Exception as e:
            print(f"Product type creation failed (attempt {i+1}): {e}")
            if i == len(input_variations) - 1:  # Last attempt
                raise RuntimeError(f"Failed to create product type after {len(input_variations)} attempts: {e}")
            continue
    
    raise RuntimeError("Failed to create product type with any input variation")

# ========= QUERIES & MUTATIONS =========

# Collections
Q_COLLECTION_BY_SLUG = """
query ($slug: String!) {
  collection(slug: $slug) { id name slug }
}
"""
M_COLLECTION_CREATE = """
mutation ($name: String!, $slug: String!) {
  collectionCreate(input: { name: $name, slug: $slug }) {
    collection { id name slug }
    errors { field code message }
  }
}
"""

# Categories
Q_CATEGORY_BY_SLUG = """
query ($slug: String!) {
  category(slug: $slug) { id name slug }
}
"""
M_CATEGORY_CREATE = """
mutation ($name: String!, $slug: String!) {
  categoryCreate(input: { name: $name, slug: $slug }) {
    category { id name slug }
    errors { field code message }
  }
}
"""

# Product Types
Q_PRODUCT_TYPE_BY_SLUG = """
query ($slug: String!) {
  productTypes(filter: { search: $slug }, first: 10) {
    edges { node { id name slug hasVariants } }
  }
}
"""

# Product Attribute Assignment
M_PRODUCT_ATTRIBUTE_ASSIGN = """
mutation AssignProductAttribute($id: ID!, $operations: [ProductAttributeAssignInput!]!) {
  productAttributeAssign(productTypeId: $id, operations: $operations) {
    errors {
      code
      field
      message
    }
    productType {
      id
      name
      slug
      productAttributes {
        id
        name
        slug
      }
    }
  }
}
"""

# Attributes
Q_ATTRIBUTE_BY_SLUG = """
query ($slug: String!) {
  attribute(slug: $slug) { id name slug inputType }
}
"""
M_ATTRIBUTE_CREATE = """
mutation ($name: String!, $slug: String!, $inputType: AttributeInputTypeEnum!, $type: AttributeTypeEnum!) {
  attributeCreate(input: { name: $name, slug: $slug, inputType: $inputType, type: $type }) {
    attribute { id name slug inputType }
    errors { field code message }
  }
}
"""

Q_ATTRIBUTE_VALUES = """
query ($id: ID!, $search: String) {
  attribute(id: $id) {
    id
    choices(first: 50, filter: { search: $search }) {
      edges { node { id name slug } }
    }
  }
}
"""
M_ATTRIBUTE_VALUE_CREATE = """
mutation ($attribute: ID!, $name: String!) {
  attributeValueCreate(attribute: $attribute, input: { name: $name }) {
    attribute { id }
    attributeValue { id name }
    errors { field code message }
  }
}
"""

# Products
M_PRODUCT_CREATE = """
mutation ($input: ProductCreateInput!) {
  productCreate(input: $input) {
    product { id name slug }
    errors { field code message }
  }
}
"""

# Variants
M_PRODUCT_VARIANT_CREATE = """
mutation ($input: ProductVariantCreateInput!) {
  productVariantCreate(input: $input) {
    productVariant { id name sku }
    errors { field code message }
  }
}
"""

# Channel listing - Using the correct mutation from network tab
M_PRODUCT_VARIANT_BULK_UPDATE = """
mutation ($product: ID!, $input: [ProductVariantBulkUpdateInput!]!, $errorPolicy: ErrorPolicyEnum) {
  productVariantBulkUpdate(
    errorPolicy: $errorPolicy
    product: $product
    variants: $input
  ) {
    errors {
      field
      code
      message
    }
    results {
      errors {
        field
        code
        message
      }
    }
  }
}
"""

# Product channel listing update
M_PRODUCT_CHANNEL_LISTING_UPDATE = """
mutation ($id: ID!, $input: ProductChannelListingUpdateInput!) {
  productChannelListingUpdate(id: $id, input: $input) {
    errors { field code message }
  }
}
"""

# Media - Fixed based on schema
M_PRODUCT_MEDIA_CREATE = """
mutation ($product: ID!, $mediaUrl: String!, $alt: String!) {
  productMediaCreate(input: { product: $product, mediaUrl: $mediaUrl, alt: $alt }) {
    product { id }
    errors { field code message }
  }
}
"""

# Tax Classes
Q_TAX_CLASSES = """
query {
  taxClasses(first: 100) {
    edges { node { id name } }
  }
}
"""

# Channels
Q_CHANNEL_BY_SLUG_DIRECT = """
query ($slug: String!) {
  channel(slug: $slug) { id name slug currencyCode }
}
"""
Q_CHANNELS_SEARCH = """
query ($q: String!) {
  channels(first: 10, filter: { search: $q }) {
    edges { node { id name slug currencyCode } }
  }
}
"""


# === Warehouses & Stocks ===
Q_WAREHOUSES_SEARCH = """
query ($q: String!) {
  warehouses(first: 10, filter: { search: $q }) {
    edges { node { id name slug } }
  }
}
"""

Q_VARIANT_STOCKS = """
query ($id: ID!) {
  productVariant(id: $id) {
    id
    stocks {
      id
      warehouse { id name }
      quantity
    }
  }
}
"""

M_VARIANT_STOCKS_CREATE = """
mutation ($variantId: ID!, $stocks: [StockInput!]!) {
  productVariantStocksCreate(variantId: $variantId, stocks: $stocks) {
    errors { field code message }
  }
}
"""

M_VARIANT_STOCKS_UPDATE = """
mutation ($variantId: ID!, $stocks: [StockInput!]!) {
  productVariantStocksUpdate(variantId: $variantId, stocks: $stocks) {
    errors { field code message }
  }
}
"""

def get_warehouse_id_by_name(name: str) -> str:
    """Find a warehouse ID by its name via search."""
    res = gql(Q_WAREHOUSES_SEARCH, {"q": name})
    edges = (res.get("warehouses") or {}).get("edges") or []
    # Prefer exact name match
    for e in edges:
        if e["node"]["name"] == name:
            return e["node"]["id"]
    if not edges:
        raise RuntimeError(f"Warehouse '{name}' not found")
    return edges[0]["node"]["id"]

def set_default_warehouse_stock(variant_id: str, qty: int = 100, warehouse_name: str = "Default Warehouse"):
    """Create or update stock for a single variant in the Default Warehouse."""
    wh_id = get_warehouse_id_by_name(warehouse_name)

    # Check current stocks for this variant
    cur = gql(Q_VARIANT_STOCKS, {"id": variant_id})
    stocks = ((cur.get("productVariant") or {}).get("stocks")) or []
    has_stock = any(s["warehouse"]["id"] == wh_id for s in stocks)

    payload = {"variantId": variant_id, "stocks": [{"warehouse": wh_id, "quantity": int(qty)}]}
    if has_stock:
        res = gql(M_VARIANT_STOCKS_UPDATE, payload)
        errs = res["productVariantStocksUpdate"]["errors"]
    else:
        res = gql(M_VARIANT_STOCKS_CREATE, payload)
        errs = res["productVariantStocksCreate"]["errors"]
    if errs:
        raise RuntimeError(f"Stock upsert error: {errs}")


# ========= HELPER FUNCTIONS =========

def _pick_product_type_by_slug(edges, slug: str):
    for edge in edges:
        if edge["node"]["slug"] == slug:
            return edge["node"]
    return None

def get_or_create_collection(slug: str, name: Optional[str] = None) -> str:
    # Check cache first
    cached_id = get_cached_id("collections", slug)
    if cached_id:
        print(f"Using cached collection: {slug} -> {cached_id}")
        return cached_id
    
    # If not in cache, make API call
    res = gql(Q_COLLECTION_BY_SLUG, {"slug": slug})
    if res.get("collection"):
        collection_id = res["collection"]["id"]
        set_cached_id("collections", slug, collection_id)
        print(f"Cached collection: {slug} -> {collection_id}")
        return collection_id
    
    # Create new collection
    name = name or slug.replace("-", " ").title()
    create = gql(M_COLLECTION_CREATE, {"name": name, "slug": slug})
    errs = create["collectionCreate"]["errors"]
    if errs:
        raise RuntimeError(f"collectionCreate error: {errs}")
    
    collection_id = create["collectionCreate"]["collection"]["id"]
    set_cached_id("collections", slug, collection_id)
    print(f"Created and cached collection: {slug} -> {collection_id}")
    return collection_id

def get_or_create_category(slug: str, name: Optional[str] = None) -> str:
    # Check cache first
    cached_id = get_cached_id("categories", slug)
    if cached_id:
        print(f"Using cached category: {slug} -> {cached_id}")
        return cached_id
    
    # If not in cache, make API call
    res = gql(Q_CATEGORY_BY_SLUG, {"slug": slug})
    if res.get("category"):
        category_id = res["category"]["id"]
        set_cached_id("categories", slug, category_id)
        print(f"Cached category: {slug} -> {category_id}")
        return category_id
    
    # Create new category
    name = name or slug.replace("-", " ").title()
    create = gql(M_CATEGORY_CREATE, {"name": name, "slug": slug})
    errs = create["categoryCreate"]["errors"]
    if errs:
        raise RuntimeError(f"categoryCreate error: {errs}")
    
    category_id = create["categoryCreate"]["category"]["id"]
    set_cached_id("categories", slug, category_id)
    print(f"Created and cached category: {slug} -> {category_id}")
    return category_id

def get_or_create_attribute(slug: str, name: Optional[str] = None, input_type: str = "DROPDOWN") -> str:
    # Check cache first
    cached_id = get_cached_id("attributes", slug)
    if cached_id:
        print(f"Using cached attribute: {slug} -> {cached_id}")
        # Validate cached ID by making a quick check
        try:
            res = gql(Q_ATTRIBUTE_BY_SLUG, {"slug": slug})
            if res.get("attribute") and res["attribute"]["id"] == cached_id:
                return cached_id
            else:
                print(f"Cached attribute ID {cached_id} is invalid, will recreate...")
                # Remove invalid cache entry
                cache = load_cache("attributes")
                if slug in cache:
                    del cache[slug]
                    save_cache("attributes", cache)
        except Exception as e:
            print(f"Error validating cached attribute {cached_id}: {e}")
            # Remove invalid cache entry
            cache = load_cache("attributes")
            if slug in cache:
                del cache[slug]
                save_cache("attributes", cache)
    
    # If not in cache or cache is invalid, make API call
    try:
        res = gql(Q_ATTRIBUTE_BY_SLUG, {"slug": slug})
        if res.get("attribute"):
            attribute_id = res["attribute"]["id"]
            set_cached_id("attributes", slug, attribute_id)
            print(f"Cached attribute: {slug} -> {attribute_id}")
            return attribute_id
    except Exception as e:
        print(f"Error looking up attribute {slug}: {e}")
    
    # Create new attribute
    name = name or slug.replace("-", " ").title()
    try:
        create = gql(M_ATTRIBUTE_CREATE, {
            "name": name, 
            "slug": slug, 
            "inputType": input_type, 
            "type": "PRODUCT_TYPE"
        })
        errs = create["attributeCreate"]["errors"]
        if errs:
            raise RuntimeError(f"attributeCreate error: {errs}")
        
        attribute_id = create["attributeCreate"]["attribute"]["id"]
        set_cached_id("attributes", slug, attribute_id)
        print(f"Created and cached attribute: {slug} -> {attribute_id}")
        return attribute_id
    except Exception as e:
        print(f"Error creating attribute {slug}: {e}")
        raise RuntimeError(f"Failed to get or create attribute {slug}: {e}")

def ensure_attribute_values(attribute_id: str, values: List[str]) -> None:
    # Load attribute values cache
    cache = load_cache("attribute_values")
    attribute_cache_key = f"{attribute_id}_values"
    cached_values = cache.get(attribute_cache_key, [])
    
    for v in values:
        # Check if value is already cached
        if v in cached_values:
            print(f"Using cached attribute value: {v} for attribute {attribute_id}")
            continue
        
        # Check if value exists in API
        search = gql(Q_ATTRIBUTE_VALUES, {"id": attribute_id, "search": v})
        existing = [edge["node"]["name"] for edge in search["attribute"]["choices"]["edges"]]
        if v in existing:
            # Add to cache
            if v not in cached_values:
                cached_values.append(v)
                cache[attribute_cache_key] = cached_values
                save_cache("attribute_values", cache)
            print(f"Found and cached existing attribute value: {v} for attribute {attribute_id}")
            continue
        
        # Create new attribute value
        create = gql(M_ATTRIBUTE_VALUE_CREATE, {"attribute": attribute_id, "name": v})
        errs = create["attributeValueCreate"]["errors"]
        if errs:
            raise RuntimeError(f"attributeValueCreate error for {v}: {errs}")
        
        # Add to cache
        if v not in cached_values:
            cached_values.append(v)
            cache[attribute_cache_key] = cached_values
            save_cache("attribute_values", cache)
        print(f"Created and cached attribute value: {v} for attribute {attribute_id}")

def assign_attributes_to_product_type(product_type_id: str, attribute_ids: List[str]) -> None:
    """Assign attributes to a product type"""
    if not attribute_ids:
        print("No attributes to assign to product type")
        return
    
    # Check cache for existing assignments
    cache = load_cache("product_type_attributes")
    cache_key = f"{product_type_id}_assigned"
    cached_assignments = cache.get(cache_key, [])
    
    # Filter out attributes that are already assigned
    new_attribute_ids = [attr_id for attr_id in attribute_ids if attr_id not in cached_assignments]
    
    if not new_attribute_ids:
        print(f"All {len(attribute_ids)} attributes are already assigned to product type {product_type_id}")
        return
    
    if len(new_attribute_ids) < len(attribute_ids):
        print(f"{len(attribute_ids) - len(new_attribute_ids)} attributes already assigned, assigning {len(new_attribute_ids)} new ones")
    
    # Create operations for attribute assignment
    operations = [{"id": attr_id, "type": "PRODUCT"} for attr_id in new_attribute_ids]
    
    print(f"Assigning {len(new_attribute_ids)} attributes to product type {product_type_id}")
    print(f"Operations: {json.dumps(operations, indent=2)}")
    
    try:
        res = gql(M_PRODUCT_ATTRIBUTE_ASSIGN, {
            "id": product_type_id,
            "operations": operations
        })
        
        errs = res["productAttributeAssign"]["errors"]
        if errs:
            print(f"Warning: Some attribute assignments failed: {errs}")
            # Check if any attributes were successfully assigned
            product_type = res.get("productAttributeAssign", {}).get("productType", {})
            if product_type:
                assigned_attrs = product_type.get("productAttributes", [])
                print(f"Successfully assigned {len(assigned_attrs)} attributes to product type")
        else:
            print(f"Successfully assigned all {len(new_attribute_ids)} attributes to product type")
            
        # Update cache with newly assigned attributes
        all_assigned = cached_assignments + new_attribute_ids
        cache[cache_key] = all_assigned
        save_cache("product_type_attributes", cache)
        print(f"Updated cache: {len(all_assigned)} total attributes assigned to product type {product_type_id}")
            
    except Exception as e:
        print(f"Error assigning attributes to product type: {e}")
        raise RuntimeError(f"Failed to assign attributes to product type: {e}")

def get_channel(slug: str) -> Tuple[str, str]:
    # returns (channel_id, currency_code)
    
    # Check cache first
    cache = load_cache("channels")
    cached_data = cache.get(slug)
    if cached_data:
        print(f"Using cached channel: {slug} -> {cached_data['id']}")
        return cached_data["id"], cached_data["currency_code"]
    
    # If not in cache, make API calls
    try:
        res = gql(Q_CHANNEL_BY_SLUG_DIRECT, {"slug": slug})
        ch = res.get("channel")
        if ch:
            channel_data = {"id": ch["id"], "currency_code": ch["currencyCode"]}
            cache[slug] = channel_data
            save_cache("channels", cache)
            print(f"Cached channel: {slug} -> {ch['id']}")
            return ch["id"], ch["currencyCode"]
    except Exception:
        pass
    
    res = gql(Q_CHANNELS_SEARCH, {"q": slug})
    for edge in res.get("channels", {}).get("edges", []):
        node = edge["node"]
        if node["slug"] == slug:
            channel_data = {"id": node["id"], "currency_code": node["currencyCode"]}
            cache[slug] = channel_data
            save_cache("channels", cache)
            print(f"Cached channel: {slug} -> {node['id']}")
            return node["id"], node["currencyCode"]
    
    raise RuntimeError(f"Channel with slug '{slug}' not found")

def get_tax_class_id(tax_class_name: str) -> Optional[str]:
    """Get tax class ID by name. Returns None if not found."""
    if not tax_class_name:
        return None
    
    # Check cache first
    cached_id = get_cached_id("tax_classes", tax_class_name.lower())
    if cached_id:
        print(f"Using cached tax class: {tax_class_name} -> {cached_id}")
        return cached_id
    
    # If not in cache, fetch from API
    try:
        res = gql(Q_TAX_CLASSES)
        for edge in res.get("taxClasses", {}).get("edges", []):
            node = edge["node"]
            if node["name"].lower() == tax_class_name.lower():
                tax_class_id = node["id"]
                set_cached_id("tax_classes", tax_class_name.lower(), tax_class_id)
                print(f"Cached tax class: {tax_class_name} -> {tax_class_id}")
                return tax_class_id
    except Exception as e:
        print(f"Error fetching tax classes: {e}")
    
    print(f"Tax class '{tax_class_name}' not found, skipping...")
    return None

def list_available_tax_classes():
    """List all available tax classes for debugging"""
    try:
        res = gql(Q_TAX_CLASSES)
        tax_classes = []
        for edge in res.get("taxClasses", {}).get("edges", []):
            node = edge["node"]
            tax_classes.append({"id": node["id"], "name": node["name"]})
        
        print("Available tax classes:")
        for tc in tax_classes:
            print(f"  - {tc['name']} (ID: {tc['id']})")
        return tax_classes
    except Exception as e:
        print(f"Error listing tax classes: {e}")
        return []

def validate_attribute_cache():
    """Validate cached attribute IDs against the actual Saleor database"""
    print("Validating attribute cache...")
    cache = load_cache("attributes")
    if not cache:
        print("No cached attributes found.")
        return
    
    # Get all attributes from Saleor
    try:
        res = gql("""
        query {
          attributes(first: 100) {
            edges { node { id name slug } }
          }
        }
        """)
        
        valid_attributes = {}
        for edge in res.get("attributes", {}).get("edges", []):
            node = edge["node"]
            valid_attributes[node["id"]] = {"name": node["name"], "slug": node["slug"]}
        
        print(f"Found {len(valid_attributes)} valid attributes in Saleor")
        
        # Check cached attributes
        invalid_count = 0
        for slug, cached_id in cache.items():
            if cached_id not in valid_attributes:
                print(f"❌ Invalid cached attribute: {slug} -> {cached_id}")
                invalid_count += 1
            else:
                print(f"✅ Valid cached attribute: {slug} -> {cached_id} ({valid_attributes[cached_id]['name']})")
        
        if invalid_count > 0:
            print(f"\nFound {invalid_count} invalid cached attributes. Clearing attribute cache...")
            clear_cache("attributes")
            print("Attribute cache cleared. Will recreate on next run.")
        else:
            print("All cached attributes are valid!")
            
    except Exception as e:
        print(f"Error validating attributes: {e}")
        print("Clearing attribute cache as precaution...")
        clear_cache("attributes")

def validate_image_mapping():
    """Validate that image mapping and files are available"""
    print("Validating image mapping and files...")
    
    # Check if mapping file exists
    mapping_file = "./images/images_and_mapping/mapping.json"
    if not os.path.exists(mapping_file):
        print(f"❌ Image mapping file not found: {mapping_file}")
        return False
    
    # Load mapping
    try:
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        print(f"✅ Image mapping loaded: {len(mapping)} entries")
    except Exception as e:
        print(f"❌ Error loading image mapping: {e}")
        return False
    
    # Check if images directory exists
    images_dir = "./images/images_and_mapping"
    if not os.path.exists(images_dir):
        print(f"❌ Images directory not found: {images_dir}")
        return False
    
    # Check sample of image files
    available_files = os.listdir(images_dir)
    image_files = [f for f in available_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
    print(f"✅ Images directory found: {len(image_files)} image files")
    
    # Check if some mapped files exist
    missing_count = 0
    found_count = 0
    for url, filename in list(mapping.items())[:10]:  # Check first 10
        file_path = os.path.join(images_dir, filename)
        if os.path.exists(file_path):
            found_count += 1
        else:
            missing_count += 1
            print(f"  ❌ Missing: {filename}")
    
    if found_count > 0:
        print(f"✅ Sample validation: {found_count} files found, {missing_count} missing")
        return True
    else:
        print(f"❌ No mapped image files found in directory")
        return False

def print_processing_config():
    """Print the current processing configuration"""
    print("⚙️  Processing Configuration:")
    print(f"   START_ROW: {START_ROW} (1-based)")
    print(f"   TOTAL_RECORDS: {TOTAL_RECORDS} (0 = all records)")
    print(f"   SKIP_HEADER: {SKIP_HEADER}")
    print(f"   CHANNEL_SLUG: {CHANNEL_SLUG}")
    print(f"   SALEOR_ENDPOINT: {SALEOR_GQL_ENDPOINT}")
    print()

# ========= PRODUCT CREATION FLOW =========

def build_editorjs_description(text: str) -> str:
    payload = {
        "time": int(time.time() * 1000),
        "blocks": [{"id": "desc1", "type": "paragraph", "data": {"text": text}}],
        "version": "2.30.7"
    }
    return json.dumps(payload, separators=(",", ":"))

def create_product(
    name: str,
    slug: str,
    description_text: str,
    category_slug: str,
    collections_slugs: List[str],
    product_type_slug: str,
    attributes_map: Dict[str, List[str]],
    rating: Optional[str] = None,
    tax_class: Optional[str] = None,
    weight: Optional[float] = None,
    skip_attributes: bool = False,  # Add option to skip attributes
):
    category_id = get_or_create_category(category_slug, name=category_slug.replace("-", " ").title())
    collection_ids = [get_or_create_collection(s, s.replace("-", " ").title()) for s in collections_slugs if s]
    product_type_id = get_or_create_product_type_fixed(product_type_slug, name=product_type_slug.replace("-", " ").title(), has_variants=True)

    # Ensure attributes (product-level) & values
    attributes_payload = []
    attribute_ids = []  # Track attribute IDs for assignment to product type
    
    if skip_attributes:
        print("⚠️  Skipping attributes as requested...")
    else:
        for attr_slug, values in attributes_map.items():
            print(f"Processing attribute: {attr_slug} with values: {values}")
            try:
                attr_id = get_or_create_attribute(attr_slug, name=attr_slug.replace("-", " ").title())
                print(f"Got attribute ID: {attr_id}")
                attribute_ids.append(attr_id)  # Add to list for product type assignment
                
                # Ensure attribute values exist
                ensure_attribute_values(attr_id, values)
                
                # Use the dropdown format based on schema (AttributeValueInput.dropdown)
                attribute_payload = {
                    "id": attr_id, 
                    "dropdown": {
                        "value": values[0] if values else ""  # Use first value for dropdown
                    }
                }
                attributes_payload.append(attribute_payload)
                print(f"Added attribute payload: {json.dumps(attribute_payload, indent=2)}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to process attribute {attr_slug}: {e}")
                print(f"   Skipping this attribute and continuing...")
                continue
        
        # Assign attributes to product type before creating the product
        if attribute_ids:
            print(f"Assigning {len(attribute_ids)} attributes to product type {product_type_id}")
            assign_attributes_to_product_type(product_type_id, attribute_ids)

    description_json_str = build_editorjs_description(description_text)

    # Get tax class ID if provided
    tax_class_id = get_tax_class_id(tax_class) if tax_class else None

    product_input = {
        "name": name,
        "slug": slug,
        "description": description_json_str,
        "category": category_id,
        "collections": collection_ids,
        "productType": product_type_id,
        "attributes": attributes_payload,
        "rating": rating if rating is not None else None,
        "taxClass": tax_class_id,
        "weight": weight if weight is not None else None,
    }
    # Remove None, empty list, and empty string values
    product_input = {k: v for k, v in product_input.items() if v not in (None, [], "")}

    print(f"Creating product with input: {json.dumps(product_input, indent=2)}")
    
    res = gql(M_PRODUCT_CREATE, {"input": product_input})
    errs = res["productCreate"]["errors"]
    if errs:
        raise RuntimeError(f"productCreate error: {errs}")
    return res["productCreate"]["product"]["id"], res["productCreate"]["product"]["slug"]

# ========= VARIANT + PRICING + MEDIA =========

def create_default_variant(product_id: str, base_slug: str, weight: Optional[float]) -> str:
    sku = f"{base_slug[:40]}-{int(time.time())}"  # simple unique-ish SKU
    name = "Default"
    input_payload = {"product": product_id, "sku": sku, "name": name, "attributes": []}
    if weight is not None:
        input_payload["weight"] = weight
    res = gql(M_PRODUCT_VARIANT_CREATE, {"input": input_payload})
    errs = res["productVariantCreate"]["errors"]
    if errs:
        raise RuntimeError(f"productVariantCreate error: {errs}")
    return res["productVariantCreate"]["productVariant"]["id"]

def set_variant_price(product_id: str, variant_id: str, channel_id: str, currency: str, price_amount: float):
    # Set variant price using the correct mutation from network tab
    input_data = [{
        "id": variant_id,
        "attributes": [],
        "stocks": {
            "create": [],
            "update": [],
            "remove": []
        },
        "channelListings": {
            "create": [{
                "channelId": channel_id,
                "price": price_amount
            }],
            "remove": [],
            "update": []
        }
    }]
    
    res = gql(M_PRODUCT_VARIANT_BULK_UPDATE, {
        "product": product_id,
        "input": input_data,
        "errorPolicy": "REJECT_FAILED_ROWS"
    })
    
    # Check for errors
    if res.get("productVariantBulkUpdate", {}).get("errors"):
        errs = res["productVariantBulkUpdate"]["errors"]
        raise RuntimeError(f"productVariantBulkUpdate error: {errs}")
    
    # Check for results errors
    results = res.get("productVariantBulkUpdate", {}).get("results", [])
    for result in results:
        if result.get("errors"):
            errs = result["errors"]
            raise RuntimeError(f"productVariantBulkUpdate result error: {errs}")

def set_product_channel_availability(product_id: str, channel_id: str, is_published: bool = True, is_available_for_purchase: bool = True):
    """Set product channel availability and publication status"""
    input_data = {
        "updateChannels": [{
            "channelId": channel_id,
            "isPublished": is_published,
            "isAvailableForPurchase": is_available_for_purchase,
            "visibleInListings": True
        }]
    }
    res = gql(M_PRODUCT_CHANNEL_LISTING_UPDATE, {"id": product_id, "input": input_data})
    errs = res["productChannelListingUpdate"]["errors"]
    if errs:
        raise RuntimeError(f"productChannelListingUpdate error: {errs}")

def add_product_media(product_id: str, url: str, alt: Optional[str] = None):
    if not url:
        return
    
    # Try to use local image mapping first
    try:
        image_mapping = load_image_mapping()
        if url in image_mapping:
            local_filename = image_mapping[url]
            local_path = os.path.join("./images/images_and_mapping", local_filename)
            
            if os.path.exists(local_path):
                print(f"Using local image: {local_filename}")
                # Determine content type from file extension
                content_type = get_content_type_from_filename(local_filename)
                upload_product_media_file(product_id, local_path, alt or "", content_type)
                return
            else:
                print(f"Local image not found: {local_path}")
                print(f"Available files in directory: {os.listdir('./images/images_and_mapping')[:10]}...")  # Show first 10 files
    except Exception as e:
        print(f"Error loading image mapping: {e}")
    
    # If local image not found, skip instead of downloading
    print(f"Image upload skipped for {url} - local file not available")

def upload_product_media_file(product_id: str, file_path: str, alt: str = "", content_type: str = "image/jpeg"):
    """Upload product media using multipart form-data"""
    
    # GraphQL mutation for product media creation
    mutation = """
    mutation ProductMediaCreate($product: ID!, $image: Upload, $alt: String) {
      productMediaCreate(
        input: {alt: $alt, image: $image, product: $product}
      ) {
        errors {
          code
          field
          message
        }
        product {
          id
          media {
            id
            alt
            url(size: 1024)
          }
        }
      }
    }
    """
    
    # Prepare the multipart form data
    operations = {
        "operationName": "ProductMediaCreate",
        "variables": {
            "alt": alt,
            "image": None,  # Will be replaced by the file
            "product": product_id
        },
        "query": mutation
    }
    
    map_data = {"1": ["variables.image"]}
    
    # Prepare files for upload
    with open(file_path, 'rb') as f:
        files = {
            'operations': (None, json.dumps(operations), 'application/json'),
            'map': (None, json.dumps(map_data), 'application/json'),
            '1': (os.path.basename(file_path), f, content_type)
        }
        
        # Make the request
        headers = {
            "Authorization": f"Bearer {SALEOR_TOKEN}",
        }
        
        print(f"Uploading file {file_path} to product {product_id}")
        response = requests.post(SALEOR_GQL_ENDPOINT, headers=headers, files=files)
        
        if response.status_code != 200:
            print(f"Upload failed with status {response.status_code}: {response.text}")
            return
        
        result = response.json()
        if "errors" in result:
            print(f"GraphQL errors: {result['errors']}")
            return
        
        data = result.get("data", {})
        if data.get("productMediaCreate", {}).get("errors"):
            errors = data["productMediaCreate"]["errors"]
            print(f"Product media creation errors: {errors}")
            return
        
        # Success
        media = data.get("productMediaCreate", {}).get("product", {}).get("media", [])
        if media:
            print(f"Successfully uploaded media: {media[-1]['url']}")  # Get the last uploaded media
        else:
            print("Media uploaded successfully but no media returned")

# ========= BULK FROM CSV =========

def parse_attributes(cell: str) -> Dict[str, List[str]]:
    """
    Expected shape in CSV:
      "key1:v1|v2;key2:v3"
    -> {"key1": ["v1","v2"], "key2": ["v3"]}
    """
    if not cell:
        return {}
    out = {}
    pairs = [p.strip() for p in str(cell).split(";") if p.strip()]
    for p in pairs:
        if ":" not in p:
            continue
        k, v = p.split(":", 1)
        values = [x.strip() for x in v.split("|") if x.strip()]
        out[slugify(k)] = values
    return out

def split_collections(cell: str) -> List[str]:
    return [slugify(s) for s in str(cell or "").split(",") if s.strip()]

def bulk_create_from_csv(csv_path: str):
    channel_id, currency = get_channel(CHANNEL_SLUG)
    created = []
    
    # Read all rows first to calculate total and handle start row
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
    
    total_rows = len(all_rows)
    print(f"📊 CSV contains {total_rows} total rows")
    
    # Calculate start and end indices
    if SKIP_HEADER:
        # If skipping header, START_ROW refers to data rows (0-based)
        start_index = START_ROW - 1  # Convert to 0-based
    else:
        # If not skipping header, START_ROW refers to actual row numbers (1-based)
        start_index = START_ROW - 1  # Convert to 0-based
    
    # Ensure start_index is within bounds
    if start_index < 0:
        start_index = 0
    if start_index >= total_rows:
        print(f"❌ START_ROW {START_ROW} is beyond the total rows ({total_rows})")
        return []
    
    # Calculate end index
    if TOTAL_RECORDS > 0:
        end_index = min(start_index + TOTAL_RECORDS, total_rows)
    else:
        end_index = total_rows
    
    rows_to_process = all_rows[start_index:end_index]
    actual_count = len(rows_to_process)
    
    print(f"🎯 Processing configuration:")
    print(f"   Start row: {START_ROW} (index {start_index})")
    print(f"   Total records to process: {TOTAL_RECORDS} (0 = all remaining)")
    print(f"   End row: {start_index + actual_count}")
    print(f"   Actual records to process: {actual_count}")
    print(f"   Skip header: {SKIP_HEADER}")
    
    if actual_count == 0:
        print("❌ No rows to process based on current configuration")
        return []
    
    print(f"\n🚀 Starting processing of {actual_count} records...")
    print("=" * 60)
    
    for i, row in enumerate(rows_to_process, 1):
        try:
            name = row["name"].strip()
            slug = slugify(row["slug"] or name)
            desc = row.get("description_text", "").strip()
            # category_slug = slugify(row["category_slug"])

            category_slug = row.get("category") or row.get("Category")
            category_slug = slugify(category_slug) if category_slug else None

            # Fallback if missing
            if not category_slug:
                # derive from product type, or use a default bucket
                category_slug = slugify(row.get("product_type") or row.get("Product Type") or "uncategorized")

            collections = split_collections(row.get("collections", ""))
            product_type_slug = slugify(row["product_type_slug"])
            attributes_map = parse_attributes(row.get("attributes", ""))
            rating = row.get("rating") or None
            tax_class = row.get("tax_class") or None
            weight = float(row["weight"]) if row.get("weight") else None
            # price = float(row["price"]) if row.get("price") else None
            price = parse_decimal(row.get("price") or row.get("Price"))

            image_url = row.get("image_url", "").strip()

            print(f"\n[{i}/{actual_count}] Processing product: {name}")
            print(f"   Product type slug: {product_type_slug}")

            # 1) Create product
            pid, pslug = create_product(
                name=name,
                slug=slug,
                description_text=desc,
                category_slug=category_slug,
                collections_slugs=collections,
                product_type_slug=product_type_slug,
                attributes_map=attributes_map,
                rating=rating,
                tax_class=tax_class,
                weight=weight,
                skip_attributes=False,  # Set to True to skip attributes completely
            )
            print(f"   ✅ Created product: {name} -> {pid}")

            # 2) Add default variant (for pricing/purchasing)
            vid = create_default_variant(pid, slug, weight)
            print(f"   ✅ Variant created: {vid}")

            # 3) Assign product to channel (required before pricing)
            set_product_channel_availability(pid, channel_id, is_published=True, is_available_for_purchase=True)
            print(f"   ✅ Product assigned to channel '{CHANNEL_SLUG}'")

            # 4) Price it in channel (if price present)
            if price is not None:
                set_variant_price(pid, vid, channel_id, currency, price)
                print(f"   ✅ Priced {price} {currency} in channel '{CHANNEL_SLUG}'")
            
            # 4.1) Always enforce stock in Default Warehouse = 100
            set_default_warehouse_stock(vid, 100, "Default Warehouse")
            print("   ✅ Stock set: Default Warehouse = 100")

            # 5) Attach image if available
            if image_url:
                add_product_media(pid, image_url, alt=name)
                print("   ✅ Image attached")

            created.append((pid, pslug, vid))
            
        except Exception as e:
            print(f"   ❌ Error processing product '{name}': {e}")
            print("   Continuing with next product...")
            continue
    
    print(f"\n" + "=" * 60)
    print(f"🎉 Processing complete!")
    print(f"   Successfully processed: {len(created)}/{actual_count} products")
    print(f"   Failed: {actual_count - len(created)} products")
                
    return created

if __name__ == "__main__":
    # Usage:
    # export SALEOR_GQL_ENDPOINT="https://your-saleor.com/graphql/"
    # export SALEOR_TOKEN="YOUR_STAFF_API_TOKEN"
    # export CHANNEL_SLUG="default-channel"
    # export START_ROW="1"                    # Start from this row (1-based)
    # export TOTAL_RECORDS="10"               # Process this many records (0 = all)
    # export SKIP_HEADER="true"               # Whether to skip header row
    # python load_products_to_saleor.py
    
    print("🚀 Starting product loading with caching enabled...")
    print_processing_config()
    print_cache_stats()
    
    # Validate image mapping and files
    print("Validating image resources...")
    image_validation = validate_image_mapping()
    if not image_validation:
        print("⚠️  Warning: Image mapping validation failed. Images may not be uploaded.")
    
    # Force clear attribute cache to fix the NOT_FOUND error
    print("Force clearing attribute cache to fix NOT_FOUND errors...")
    clear_cache("attributes")
    clear_cache("attribute_values")
    print("Attribute caches cleared. Will recreate on next run.")
    
    # List available tax classes for debugging
    print("Checking available tax classes...")
    list_available_tax_classes()
    
    # Validate attribute cache
    validate_attribute_cache()
    
    csv_file = "../../data/saleor_products_ready_enriched.csv"  # adjust path if needed
    results = bulk_create_from_csv(csv_file)
    
    print(f"\n🎉 Done. Created {len(results)} product(s) with variants, pricing, and images.")
    print("\nFinal cache statistics:")
    print_cache_stats()
