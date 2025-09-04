#!/bin/bash

# Neo4j Search Test Script
# This script tests the enhanced search capabilities

echo "🔍 Testing Neo4j Search Capabilities..."

# Activate virtual environment and run search tests
source .venv/bin/activate && PYTHONPATH=. python -c "
import asyncio
from scripts.load_products_to_neo4j import test_neo4j_search
asyncio.run(test_neo4j_search())
"

echo "✅ Neo4j Search Tests completed!"
