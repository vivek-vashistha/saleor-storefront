#!/usr/bin/env python3
"""
Saleor GraphQL Schema Introspection Script
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========= CONFIG =========
SALEOR_GQL_ENDPOINT = os.getenv("SALEOR_GQL_ENDPOINT", "https://your-saleor.com/graphql/")
SALEOR_TOKEN = os.getenv("SALEOR_TOKEN", "REPLACE_ME")

def introspect_schema():
    """Get the complete GraphQL schema"""
    
    print("=== Saleor GraphQL Schema Introspection ===")
    
    # Full introspection query
    introspection_query = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          ...FullType
        }
        directives {
          name
          description
          locations
          args {
            ...InputValue
          }
        }
      }
    }

    fragment FullType on __Type {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          ...InputValue
        }
        type {
          ...TypeRef
        }
        isDeprecated
        deprecationReason
      }
      inputFields {
        ...InputValue
      }
      interfaces {
        ...TypeRef
      }
      enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes {
        ...TypeRef
      }
    }

    fragment InputValue on __InputValue {
      name
      description
      type { ...TypeRef }
      defaultValue
    }

    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SALEOR_TOKEN}",
    }
    
    payload = {"query": introspection_query}
    
    print(f"Making introspection request to: {SALEOR_GQL_ENDPOINT}")
    
    try:
        r = requests.post(SALEOR_GQL_ENDPOINT, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            return None
            
        return data["data"]["__schema"]
        
    except Exception as e:
        print(f"Error during introspection: {e}")
        return None

def analyze_mutations(schema):
    """Analyze the schema to find relevant mutations"""
    
    print("\n=== Analyzing Mutations ===")
    
    mutations = {}
    
    for type_info in schema["types"]:
        if type_info["name"] == "Mutation":
            print(f"Found Mutation type with {len(type_info['fields'])} fields")
            
            for field in type_info["fields"]:
                field_name = field["name"]
                
                # Focus on product-related mutations
                if any(keyword in field_name.lower() for keyword in ["product", "variant", "media", "channel"]):
                    mutations[field_name] = {
                        "name": field_name,
                        "description": field.get("description", ""),
                        "args": []
                    }
                    
                    for arg in field["args"]:
                        mutations[field_name]["args"].append({
                            "name": arg["name"],
                            "type": get_type_string(arg["type"]),
                            "description": arg.get("description", "")
                        })
    
    return mutations

def analyze_input_types(schema):
    """Analyze input types for product operations"""
    
    print("\n=== Analyzing Input Types ===")
    
    input_types = {}
    
    for type_info in schema["types"]:
        if type_info["kind"] == "INPUT_OBJECT":
            type_name = type_info["name"]
            
            # Focus on product-related input types
            if any(keyword in type_name.lower() for keyword in ["product", "variant", "media", "channel", "attribute"]):
                input_types[type_name] = {
                    "name": type_name,
                    "description": type_info.get("description", ""),
                    "fields": []
                }
                
                for field in type_info["inputFields"]:
                    input_types[type_name]["fields"].append({
                        "name": field["name"],
                        "type": get_type_string(field["type"]),
                        "description": field.get("description", ""),
                        "defaultValue": field.get("defaultValue")
                    })
    
    return input_types

def get_type_string(type_info):
    """Convert type info to string representation"""
    if type_info["kind"] == "NON_NULL":
        return f"{get_type_string(type_info['ofType'])}!"
    elif type_info["kind"] == "LIST":
        return f"[{get_type_string(type_info['ofType'])}]"
    else:
        return type_info["name"]

def print_mutation_details(mutations):
    """Print detailed mutation information"""
    
    print("\n=== Product-Related Mutations ===")
    
    for mutation_name, mutation_info in mutations.items():
        print(f"\n🔧 {mutation_name}")
        if mutation_info["description"]:
            print(f"   Description: {mutation_info['description']}")
        
        print("   Arguments:")
        for arg in mutation_info["args"]:
            print(f"     - {arg['name']}: {arg['type']}")
            if arg["description"]:
                print(f"       {arg['description']}")

def print_input_type_details(input_types):
    """Print detailed input type information"""
    
    print("\n=== Product-Related Input Types ===")
    
    for type_name, type_info in input_types.items():
        print(f"\n📝 {type_name}")
        if type_info["description"]:
            print(f"   Description: {type_info['description']}")
        
        print("   Fields:")
        for field in type_info["fields"]:
            required = "!" if field["type"].endswith("!") else ""
            print(f"     - {field['name']}: {field['type']}{required}")
            if field["description"]:
                print(f"       {field['description']}")
            if field["defaultValue"]:
                print(f"       Default: {field['defaultValue']}")

def save_schema_to_file(schema, filename="saleor_schema.json"):
    """Save the schema to a file for reference"""
    
    with open(filename, 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"\n💾 Schema saved to {filename}")

if __name__ == "__main__":
    print("Starting Saleor GraphQL schema introspection...")
    
    # Get the schema
    schema = introspect_schema()
    
    if schema:
        print("✅ Schema introspection successful!")
        
        # Save schema to file
        save_schema_to_file(schema)
        
        # Analyze mutations
        mutations = analyze_mutations(schema)
        print_mutation_details(mutations)
        
        # Analyze input types
        input_types = analyze_input_types(schema)
        print_input_type_details(input_types)
        
        print(f"\n🎉 Schema analysis complete!")
        print(f"Found {len(mutations)} product-related mutations")
        print(f"Found {len(input_types)} product-related input types")
        
    else:
        print("❌ Schema introspection failed!")
        sys.exit(1)
