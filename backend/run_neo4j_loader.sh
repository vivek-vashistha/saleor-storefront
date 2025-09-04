#!/bin/bash

# Neo4j Product Loader Script
# This script loads products into Neo4j with enhanced graph relationships

echo "🚀 Starting Neo4j Product Loader..."

# Activate virtual environment and run the loader
source .venv/bin/activate && PYTHONPATH=. python scripts/load_products_to_neo4j.py

echo "✅ Neo4j Product Loader completed!"
