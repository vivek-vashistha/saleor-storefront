import logging
from typing import Dict, List, Optional, Any

from backend.domain.entities import Product
from backend.infrastructure.connections.saleor.interface import ISaleorConnection

logger = logging.getLogger("conversational_commerce")


class SaleorService:
    """Service for handling Saleor-related functionality."""

    def __init__(self, saleor_connection: ISaleorConnection):
        """Initialize the Saleor service.

        Args:
            saleor_connection: Connection to Saleor API
        """
        self.saleor_connection = saleor_connection

    async def enrich_products_with_saleor_data(self, products: List[Product]) -> List[Product]:
        """Enrich products with additional data from Saleor.

        Args:
            products: List of products to enrich

        Returns:
            List of enriched products
        """
        if not products:
            logger.info("No products to enrich with Saleor data")
            return products

        logger.info(f"Enriching {len(products)} products with Saleor data using batch request")
        
        # Extract product IDs and names for logging
        product_ids = [str(product.product_id) for product in products]
        product_names = [product.name for product in products]
        
        
        logger.info(f"Product IDs array: {product_ids}")
        logger.info(f"Product names array: {product_names}")
        
        try:
            # Extract just the product IDs for kg_products (like in test script)
            # Map our system IDs to Saleor IDs for the API call
            product_ids_for_batch = [str(p.product_id) for p in products]
            
            # Use the mapped Saleor IDs for the API call
            saleor_response = await self.saleor_connection.get_products_batch_simple(product_ids_for_batch)
            
            if saleor_response:
                logger.info(f"Successfully received batch response from Saleor for {len(products)} products")
                logger.info(f"Saleor response: {saleor_response}\n\n")
                # Log Saleor response details separately for better readability
                if 'answer' in saleor_response:
                    answer = saleor_response['answer']
                    logger.info("=== Saleor Response Breakdown ===")
                    
                    # Extract and log inputs
                    if '### Inputs' in answer:
                        inputs_start = answer.find('### Inputs')
                        inputs_end = answer.find('### Generated queries')
                        if inputs_end == -1:
                            inputs_end = answer.find('### Tool call responses')
                        if inputs_end == -1:
                            inputs_end = answer.find('### Final response')
                        
                        if inputs_end != -1:
                            inputs_section = answer[inputs_start:inputs_end].strip()
                            logger.info(f"Inputs: {inputs_section}")
                    
                    # Extract and log generated queries
                    if '### Generated queries' in answer:
                        queries_start = answer.find('### Generated queries')
                        queries_end = answer.find('### Tool call responses')
                        if queries_end == -1:
                            queries_end = answer.find('### Final response')
                        
                        if queries_end != -1:
                            queries_section = answer[queries_start:queries_end].strip()
                            logger.info(f"Generated Queries: {queries_section}")
                    
                    # Extract and log tool call responses
                    if '### Tool call responses' in answer:
                        tool_start = answer.find('### Tool call responses')
                        tool_end = answer.find('### Final response')
                        
                        if tool_end != -1:
                            tool_section = answer[tool_start:tool_end].strip()
                            logger.info(f"Tool Call Responses: {tool_section}")
                    
                    # Extract and log final response
                    if '### Final response' in answer:
                        final_start = answer.find('### Final response')
                        final_section = answer[final_start:].strip()
                        logger.info(f"Final Response: {final_section}")
                    
                    logger.info("=== End Saleor Response Breakdown ===")
                
                # Log other response details
                if 'session_id' in saleor_response:
                    logger.info(f"Session ID: {saleor_response['session_id']}")
                if 'info' in saleor_response and 'response_time' in saleor_response['info']:
                    logger.info(f"Response Time: {saleor_response['info']['response_time']}s")
                
                # Try to use structured products if present for deterministic mapping
                structured_products = saleor_response.get('structured_products') if isinstance(saleor_response, dict) else None
                id_to_price: dict[str, float] = {}
                id_to_currency: dict[str, str] = {}
                if structured_products and isinstance(structured_products, list):
                    for item in structured_products:
                        try:
                            pid = str(item.get('id'))
                            price = ((item.get('price') or {}).get('amount'))
                            currency = ((item.get('price') or {}).get('currency'))
                            if pid is not None and price is not None:
                                id_to_price[pid] = float(price)
                                if currency:
                                    id_to_currency[pid] = str(currency)
                        except Exception:
                            continue

                # Enrich all products with structured data when available; fallback to text parsing
                enriched_products = []
                for product in products:
                    pid = str(product.product_id)
                    if pid in id_to_price:
                        enriched_product = product.model_copy()
                        enriched_product.saleor_data = saleor_response
                        enriched_product.price = id_to_price[pid]
                        logger.info(f"Updated product '{product.name}' (ID: {product.product_id}) price to {id_to_price[pid]} from structured Saleor data")
                    else:
                        enriched_product = self._enrich_product(product, saleor_response)
                    enriched_products.append(enriched_product)
                
                logger.info(f"Successfully enriched {len(enriched_products)} products with Saleor batch data")
                return enriched_products
            else:
                logger.warning("Batch request to Saleor failed")
                return products  # Return original products if no response
                
        except Exception as e:
            logger.error(f"Error in batch enrichment: {e}")
            return products  # Return original products on error



    def _enrich_product(self, product: Product, saleor_data: Dict[str, Any]) -> Product:
        """Enrich a product with Saleor data.

        Args:
            product: Original product
            saleor_data: Saleor product data

        Returns:
            Enriched product
        """
        # Create a copy of the product to avoid modifying the original
        enriched_product = product.model_copy()
        
        # Add Saleor data as an attribute
        enriched_product.saleor_data = saleor_data
        
        # Try to find and update the product price from Saleor data
        try:
            if 'answer' in saleor_data:
                answer = saleor_data['answer']
                
                # Look for the product in the tool call responses section
                if '### Tool call responses' in answer and '### Final response' in answer:
                    tool_section = answer[answer.find('### Tool call responses'):answer.find('### Final response')]
                    
                    saleor_id = str(product.product_id)
                    if saleor_id in tool_section:
                        # Extract price from the response
                        price_pattern = f"**{product.name}** (ID: {saleor_id})"
                        if price_pattern in tool_section:
                            # Find the price line after this product
                            lines = tool_section.split('\n')
                            for i, line in enumerate(lines):
                                if price_pattern in line:
                                    # Look for price in next few lines
                                    for j in range(i+1, min(i+5, len(lines))):
                                        price_line = lines[j].strip()
                                        if 'Price:' in price_line and 'USD' in price_line:
                                            try:
                                                # Extract price value
                                                price_str = price_line.split('USD')[1].strip()
                                                saleor_price = float(price_str)
                                                
                                                # Update the product price
                                                enriched_product.price = saleor_price
                                                logger.info(f"Updated product '{product.name}' (ID: {product.product_id}) price from ${product.price} to ${saleor_price} using Saleor data")
                                                break
                                            except (ValueError, IndexError):
                                                logger.warning(f"Could not parse price from line: {price_line}")
                                            break
                                        elif 'Price:' in price_line:
                                            # Alternative price format
                                            try:
                                                price_str = price_line.split('Price:')[1].strip()
                                                if 'USD' in price_str:
                                                    price_str = price_str.split('USD')[1].strip()
                                                saleor_price = float(price_str)
                                                
                                                # Update the product price
                                                enriched_product.price = saleor_price
                                                logger.info(f"Updated product '{product.name}' (ID: {product.product_id}) price from ${product.price} to ${saleor_price} using Saleor data (alternative format)")
                                                break
                                            except (ValueError, IndexError):
                                                logger.warning(f"Could not parse price from line (alternative format): {price_line}")
                                            break
                                    break
                    else:
                        logger.info(f"No Saleor price found for product '{product.name}' (ID: {product.product_id}), keeping original price: ${product.price}")
                        
        except Exception as e:
            logger.warning(f"Error updating price for product '{product.name}' (ID: {product.product_id}): {e}")
            logger.info(f"Keeping original price: ${product.price}")
        
        return enriched_product

    async def get_saleor_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details from Saleor by ID.

        Args:
            product_id: Product ID to look up

        Returns:
            Saleor product data if found, None otherwise
        """
        try:
            logger.info(f"Fetching Saleor details for product ID: {product_id}")
            saleor_data = await self.saleor_connection.get_product_by_id(product_id)
            
            if saleor_data:
                logger.info(f"Successfully fetched Saleor data for product ID: {product_id}")
                return saleor_data
            else:
                logger.warning(f"No Saleor data found for product ID: {product_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Saleor data for product ID {product_id}: {e}")
            return None

    async def get_saleor_product_details_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get product details from Saleor by name.

        Args:
            product_name: Product name to look up

        Returns:
            Saleor product data if found, None otherwise
        """
        try:
            logger.info(f"Fetching Saleor details for product name: {product_name}")
            saleor_data = await self.saleor_connection.get_product_by_name(product_name)
            
            if saleor_data:
                logger.info(f"Successfully fetched Saleor data for product name: {product_name}")
                return saleor_data
            else:
                logger.warning(f"No Saleor data found for product name: {product_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Saleor data for product name {product_name}: {e}")
            return None
