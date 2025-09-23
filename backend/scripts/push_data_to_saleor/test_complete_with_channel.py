#!/usr/bin/env python3
"""
Complete product creation test with channel availability and pricing
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import the fixed script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions from the fixed script
from load_products_to_saleor_fixed import (
    create_product,
    create_default_variant,
    set_variant_price,
    set_product_channel_availability,
    add_product_media,
    get_channel
)

def test_complete_with_channel():
    """Test creating a complete product with channel availability and pricing"""
    
    print("=== Complete Product Creation Test (With Channel Availability) ===")
    
    try:
        # Get channel info
        print("\n1. Getting channel information...")
        channel_id, currency = get_channel("default-channel")
        print(f"✅ Channel: {channel_id}, Currency: {currency}")
        
        # Test product data
        import time
        timestamp = int(time.time())
        test_product = {
            "name": f"Complete Channel Product {timestamp}",
            "slug": f"complete-channel-product-{timestamp}",
            "description_text": "This is a complete test product with channel availability and pricing.",
            "category_slug": "test-category",
            "collections_slugs": ["test-collection"],
            "product_type_slug": "test-product-type-2",
            "attributes_map": {},  # No attributes for now
            "rating": "4.5",
            "weight": 1.5,
            "price": 89.99,
            "image_url": "https://via.placeholder.com/300x300?text=Complete+Channel+Product"
        }
        
        print(f"\n2. Creating product: {test_product['name']}")
        product_id, product_slug = create_product(
            name=test_product["name"],
            slug=test_product["slug"],
            description_text=test_product["description_text"],
            category_slug=test_product["category_slug"],
            collections_slugs=test_product["collections_slugs"],
            product_type_slug=test_product["product_type_slug"],
            attributes_map=test_product["attributes_map"],
            rating=test_product["rating"],
            weight=test_product["weight"]
        )
        print(f"✅ Product created: {product_id} (slug: {product_slug})")
        
        print("\n3. Creating default variant...")
        variant_id = create_default_variant(product_id, product_slug, test_product["weight"])
        print(f"✅ Variant created: {variant_id}")
        
        print("\n4. Setting product channel availability...")
        set_product_channel_availability(
            product_id, 
            channel_id, 
            is_published=True, 
            is_available_for_purchase=True
        )
        print(f"✅ Product made available in channel")
        
        print("\n5. Setting variant price...")
        set_variant_price(product_id, variant_id, channel_id, currency, test_product["price"])
        print(f"✅ Price set: {test_product['price']} {currency}")
        
        print("\n6. Adding product media...")
        add_product_media(product_id, test_product["image_url"], test_product["name"])
        print("✅ Media added")
        
        print(f"\n🎉 COMPLETE SUCCESS! All features working!")
        print(f"Product ID: {product_id}")
        print(f"Product Slug: {product_slug}")
        print(f"Variant ID: {variant_id}")
        print(f"Price: {test_product['price']} {currency}")
        print(f"Channel: Default Channel")
        print(f"Status: Published and Available for Purchase")
        print(f"Media: {test_product['image_url']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during complete product creation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_with_channel()
    if success:
        print("\n🎉 PERFECT! Complete product creation with channel availability is working!")
        print("All features confirmed:")
        print("  ✅ Product creation")
        print("  ✅ Variant creation")
        print("  ✅ Channel availability")
        print("  ✅ Product publication")
        print("  ✅ Pricing")
        print("  ✅ Media")
        print("\nYou can now run the full product import with confidence!")
        print("Run: python load_products_to_saleor_fixed.py")
    else:
        print("\n❌ Complete product creation still has issues.")
        sys.exit(1)
