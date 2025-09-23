from fastapi import status

from backend.application.interfaces import IChatWorkflow
from backend.application.services import ProductService, OrderGraphService
from backend.domain.entities import ChatSession, ChatState, SearchQuery
from backend.domain.exceptions import ServiceError
from backend.infrastructure.repositories import IChatSessionRepository


class CreateChatSessionUseCase:
    """Use case for creating a new chat session."""

    def __init__(self, chat_session_repository: IChatSessionRepository):
        """Initialize the CreateChatSessionUseCase with the provided repository.

        Args:
            chat_session_repository: Chat session repository
        """
        self.chat_session_repository = chat_session_repository

    async def execute(self, user_id: str) -> ChatSession:
        """Execute the use case to create a new chat session.

        Args:
            user_id: The ID of the user

        Returns:
            The created chat session
        """
        # Create a new chat session
        session = ChatSession(user_id=user_id)
         # Try to hydrate the new session with any existing user profile
        # from the user's most recent session (to persist memory across sessions)
        try:
            previous_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            if previous_sessions:
                # Pick the most recently updated session
                latest_session = max(previous_sessions, key=lambda s: s.updated_at)
                # If the latest session has any user profile info, carry it over
                if getattr(latest_session.state, "has_user_profile", False):
                    session.state.user_profile = latest_session.state.user_profile
                # Optionally carry user_id into state for consistency
                session.state.user_id = user_id
        except Exception:
            # If anything goes wrong, continue with a fresh profile
            pass
        return await self.chat_session_repository.create_session(session)


class GetChatSessionUseCase:
    """Use case for retrieving a chat session."""

    def __init__(self, chat_session_repository: IChatSessionRepository):
        """Initialize the GetChatSessionUseCase with the provided repository.

        Args:
            chat_session_repository: Chat session repository
        """
        self.chat_session_repository = chat_session_repository

    async def execute(self, session_id: str) -> ChatSession:
        """Execute the use case to retrieve a chat session.

        Args:
                    session_id: The ID of the chat session to
        # Exception handler for ServiceError
        @router.exception_handler(ServiceError)
        async def service_error_handler(request: Request, exc: ServiceError):
            return exc.get_error_response() retrieve

        Returns:
                    The chat session if found

        Raises:
                    ServiceError: If the session is not found
        """
        session = await self.chat_session_repository.get_session(session_id)
        if not session:
            raise ServiceError(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID {session_id} not found")
        return session


class UpdateChatSessionUseCase:
    """Use case for updating a chat session."""

    def __init__(self, chat_session_repository: IChatSessionRepository):
        """Initialize the UpdateChatSessionUseCase with the provided repository.

        Args:
            chat_session_repository: Chat session repository
        """
        self.chat_session_repository = chat_session_repository

    async def execute(self, session: ChatSession) -> ChatSession:
        """Execute the use case to update a chat session.

        Args:
            session: The chat session to update

        Returns:
            The updated chat session
        """
        return await self.chat_session_repository.update_session(session)


class ProcessChatMessageUseCase:
    """Use case for processing a message in a chat session."""

    def __init__(
        self,
        chat_session_repository: IChatSessionRepository,
        workflow: IChatWorkflow[ChatState],
        product_service: ProductService,
        order_graph_service: OrderGraphService = None,
        llm=None,
    ):
        """Initialize the ProcessChatMessageUseCase.

        Args:
            chat_session_repository: Chat session repository
            workflow: The chat workflow for processing messages
            product_service: Service for product-related functionality
            order_graph_service: Service for order-related graph API interactions
            llm: Language model instance for LLM operations
        """
        self.chat_session_repository = chat_session_repository
        self.workflow = workflow
        self.product_service = product_service
        self.order_graph_service = order_graph_service
        self.llm = llm

    async def execute(
        self, session: ChatSession, message_content: str, referenced_product_ids: list[int] | None = None
    ) -> tuple[ChatSession, int]:
        """Execute the use case to process a chat message.

        Args:
            session: The chat session where the message will be added
            message_content: The content of the message
            referenced_product_ids: Optional list of product IDs referenced in the message

        Returns:
            A tuple containing the updated chat session and the index of the first new message
        """
        import logging
        logger = logging.getLogger("conversational_commerce")
        
        # Verify session exists
        if not session or not session.id:
            raise ServiceError(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid chat session")

        logger.info(f"Processing message: '{message_content}' for session {session.id}")

        # Check if this is an order-related query FIRST
        is_order_query = await self._is_order_query(message_content, session)
        logger.info(f"Order query detection result: {is_order_query}")

        # Add the human message to the session
        session.add_message(message_content)

        # Store the current message count to determine where new messages start
        message_index = len(session.state.messages)

        # Handle referenced products if provided
        if referenced_product_ids:
            # Get referenced products from the product service
            referenced_products = await self.product_service.get_products_by_ids(referenced_product_ids)
            # Add referenced products to the state
            session.state.referenced_products = referenced_products
        else:
            # Reset referenced products if no products are referenced
            session.state.referenced_products = []

        # If it's an order query, handle it immediately and skip product processing
        if is_order_query:
            logger.info("Handling order query - skipping product processing")
            await self._handle_order_queries(session, message_content)
        else:
            logger.info("Processing as product query")
            
            # Log user profile information if available
            if session.state.has_user_profile:
                # logger.info(f"User profile available: {session.state.user_profile.get_relevant_context('general')}")
                profile = session.state.user_profile
                logger.info(
                    "User profile available: "
                    f"email={profile.email}, "
                    f"health_conditions={profile.health_conditions}, "
                    f"activity_preferences={profile.activity_preferences}, "
                    f"product_preferences={profile.product_preferences}, "
                    f"budget_range={profile.budget_range}"
                )

                # If we already have the user's email, proactively fetch order context once
                try:
                    email_present = bool((profile.email or '').strip())
                    already_added_orders = any(
                        isinstance(msg.get('content', ''), str) and ('order' in msg.get('content', '').lower())
                        for msg in session.state.messages
                    )
                    if email_present and not already_added_orders:
                        logger.info("Email present in profile; preloading user's order status context")
                        await self._handle_order_queries(session, "orders details")    # users query as order details
                except Exception as preload_err:
                    logger.warning(f"Failed to preload orders context: {preload_err}")
            else:
                logger.info("No user profile information available")
            
            # Process the message with the workflow
            workflow_name = self.workflow.__class__.__name__
            logger.info(f"[PROCESS_CHAT] Using workflow: {workflow_name}")
            session.state = await self.workflow.run(session.state)
            logger.info(f"[PROCESS_CHAT] Workflow {workflow_name} completed")

            # Get products based on user intent, not just number of queries
            if session.state.has_search_query:
                logger.info(f"Found {len(session.state.search_queries)} search queries to process")
                
                # Log all search queries
                for i, query in enumerate(session.state.search_queries):
                    logger.info(f"Search Query {i+1}: '{query.query}' -> categories: {query.categories}")
                
                # Use LLM to determine if user wants bundles or individual products
                should_bundle = await self._determine_bundling_intent_with_llm(session.state, message_content)
                logger.info(f"LLM determined bundling intent: {should_bundle}")
                
                if should_bundle:
                    logger.info("LLM determined user wants bundles - creating intelligent product bundles")
                    product_bundles = await self.product_service.get_intelligent_product_bundles(
                        session.state.search_queries, 
                        user_profile=session.state.user_profile,
                        max_bundles=3
                    )

                    if product_bundles:
                        logger.info(f"Created {len(product_bundles)} intelligent product bundles")
                        # Add the product bundles to the AI message
                        session.add_ai_message_with_product_bundles(product_bundles)
                    else:
                        logger.warning("No intelligent product bundles created")
                else:
                    logger.info("LLM determined user wants individual products - getting product list")
                    products = await self.product_service.get_products_for_query(
                        session.state.search_queries[0], max_num_results=5
                    )

                    if products:
                        logger.info(f"Retrieved {len(products)} individual products")
                        session.add_ai_message_with_products(products)
                    else:
                        logger.warning("No products retrieved for single query")
            else:
                logger.info("No search queries generated - no products to retrieve")

        # Log AI responses generated for this user message
        try:
            new_messages = session.state.messages[message_index:]
            for i, m in enumerate(new_messages, start=1):
                msg_type = m.get("type", "ai")
                if msg_type == "ai":
                    content = m.get("content", "")
                    if isinstance(content, list):
                        text = " ".join([str(x) for x in content if isinstance(x, (str, int, float))])
                    else:
                        text = str(content)
                    logger.info(f"\n\nAI response {i}: {text}\n\n")
                elif msg_type == "product_recommendation":
                    prods = m.get("recommended_products", []) or []
                    names = [p.get("name") for p in prods if isinstance(p, dict) and p.get("name")]
                    logger.info(f"\nAI product recommendation ({len(names)}): {names}")
                elif msg_type == "product_bundle_recommendation":
                    bundles = m.get("recommended_bundles", []) or []
                    bundle_info = []
                    for b in bundles:
                        if isinstance(b, dict):
                            label = b.get("category") or b.get("name") or "bundle"
                            products = b.get("products", []) or []
                            bundle_info.append(f"{label}({len(products)})")
                    logger.info(f"\nAI bundle recommendation ({len(bundles)}): {bundle_info}")
        except Exception as log_err:
            logger.warning(f"\nFailed to log AI responses: {log_err}")

        # Update the session in the repository
        updated_session = await self.chat_session_repository.update_session(session)

        return updated_session, message_index

    async def _determine_bundling_intent_with_llm(self, state, message_content: str) -> bool:
        """Use LLM to determine if user wants bundles or individual products.
        
        Args:
            state: The chat state with user profile and conversation history
            message_content: The current user message
            
        Returns:
            Boolean indicating whether to create bundles (True) or individual products (False)
        """
        import logging
        logger = logging.getLogger("conversational_commerce")
        
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            from pydantic import BaseModel, Field
            
            # Define the response structure
            class BundlingIntent(BaseModel):
                should_bundle: bool = Field(description="Whether the user wants product bundles (True) or individual products (False)")
                reasoning: str = Field(description="Brief explanation of the decision")
                confidence: float = Field(description="Confidence score from 0.0 to 1.0")
            
            # Get conversation context
            conversation_history = []
            for msg in state.messages[-5:]:  # Last 5 messages for context
                if isinstance(msg.get('content'), str):
                    role = "User" if msg.get('type') == 'human' else "Assistant"
                    conversation_history.append(f"{role}: {msg.get('content')}")
            
            conversation_context = "\n".join(conversation_history)
            
            # Get user profile context
            user_profile_context = ""
            if state.user_profile:
                profile = state.user_profile
                if profile.budget_range:
                    user_profile_context += f"Budget: {profile.budget_range}\n"
                if profile.health_conditions:
                    user_profile_context += f"Health conditions: {', '.join(profile.health_conditions)}\n"
                if profile.product_preferences:
                    user_profile_context += f"Product preferences: {', '.join(profile.product_preferences)}\n"
                if profile.activity_preferences:
                    user_profile_context += f"Activity preferences: {', '.join(profile.activity_preferences)}\n"
            
            # Create the prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert e-commerce assistant that determines whether a user wants product bundles or individual products.

BUNDLES are appropriate when:
- User asks for a "complete solution", "everything I need", "full setup"
- User mentions specific use cases like "camping trip", "workout routine", "sleep routine"
- User has budget constraints and wants a comprehensive solution
- User asks for "kits", "packages", "bundles", "complete sets"
- User is a beginner asking for "everything to get started"
- User wants products that work together (e.g., sleep supplements + sleep aids)

INDIVIDUAL PRODUCTS are appropriate when:
- User asks for specific products: "best melatonin", "protein powder", "vitamin D"
- User asks "what", "which", "recommend" for a single product type
- User wants to compare options within a category
- User asks for "suggestions" or "recommendations" for one product type
- User is looking for alternatives or specific features

Consider the user's profile, conversation history, and current message to make an intelligent decision.

Respond with JSON format: {"should_bundle": boolean, "reasoning": "explanation", "confidence": 0.0-1.0}"""),
                ("human", """Conversation History:
{conversation_context}

User Profile:
{user_profile_context}

Current Message: "{current_message}"

Based on this context, determine if the user wants product bundles or individual products.""")
            ])
            
            # Use the injected LLM instance or create a new one with proper API key
            if self.llm:
                llm = self.llm
            else:
                # Fallback: try to get API key from environment
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=api_key)
            
            parser = JsonOutputParser(pydantic_object=BundlingIntent)
            
            # Create the chain
            chain = prompt | llm | parser
            
            # Get the result
            result = await chain.ainvoke({
                "conversation_context": conversation_context,
                "user_profile_context": user_profile_context,
                "current_message": message_content
            })
            
            logger.info(f"LLM bundling analysis: {result}")
            
            # Return the decision with confidence threshold
            return result.should_bundle if result.confidence > 0.6 else False
            
        except Exception as e:
            logger.error(f"Error in LLM bundling analysis: {e}")
            # Fallback: use simple heuristic based on message content
            message_lower = message_content.lower()
            bundle_indicators = ['complete', 'everything', 'all', 'kit', 'bundle', 'package', 'solution']
            individual_indicators = ['specific', 'just', 'only', 'single', 'recommend', 'best']
            
            bundle_score = sum(1 for indicator in bundle_indicators if indicator in message_lower)
            individual_score = sum(1 for indicator in individual_indicators if indicator in message_lower)
            
            logger.info(f"Fallback analysis: bundle_score={bundle_score}, individual_score={individual_score}")
            return bundle_score > individual_score

    async def _is_order_query(self, message_content: str, session: ChatSession = None) -> bool:
        """Check if the message is order-related.

        Args:
            message_content: The message content to check
            session: Optional chat session to check for order context

        Returns:
            True if the message is order-related, False otherwise
        """
        import logging
        import re
        logger = logging.getLogger("conversational_commerce")
        
        # Comprehensive list of order-related keywords and phrases
        order_keywords = [
            'order', 'orders', 'status', 'tracking', 'delivery', 'shipping',
            'purchase', 'bought', 'my order', 'order status', 'order tracking',
            'where is my order', 'when will my order arrive', 'order delivery',
            'shipping status', 'delivery status', 'track my order', 'order info',
            'my purchase', 'purchase status', 'order details', 'order history',
            'recent orders', 'order confirmation', 'order number', 'order id',
            'check order', 'find order', 'locate order', 'order inquiry'
        ]
        
        message_lower = message_content.lower()
        is_order_query = any(keyword in message_lower for keyword in order_keywords)
        
        # Check if this is an email response to a previous order query
        if not is_order_query and session and session.state.messages:
            # Look for recent AI messages asking for email
            recent_ai_messages = []
            logger.info(f"Total messages in session: {len(session.state.messages)}")
            
            # Check all messages, not just the last 10
            for i, msg in enumerate(session.state.messages):
                # Check the message type - HumanMessage has type="human", AIMessage has type="ai"
                msg_type = msg.get('type', 'human')
                is_human = msg_type == 'human'
                content = msg.get('content', '')
                
                # Handle content that might be a list or string
                if isinstance(content, list):
                    # If content is a list, join all items
                    content_str = ' '.join(str(item) for item in content)
                else:
                    content_str = str(content)
                
                logger.info(f"Message {i}: type='{msg_type}', is_human={is_human}, content='{content_str[:50]}...'")
                if not is_human:  # AI message
                    recent_ai_messages.append(content_str.lower())
            
            logger.info(f"Recent AI messages: {recent_ai_messages}")
            
            # Check if any recent AI message asked for email for order status
            asked_for_email = any(
                'email' in msg and ('order' in msg or 'status' in msg or 'check' in msg or 'help' in msg or 'provide' in msg) 
                for msg in recent_ai_messages
            )
            
            logger.info(f"Asked for email: {asked_for_email}")
            
            if asked_for_email:
                # Check if current message looks like an email address or contains an email
                email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
                if re.search(email_pattern, message_content.strip()):
                    logger.info(f"Detected email response to order query: {message_content}")
                    return True
        
        logger.info(f"Order query detection - Message: '{message_content}', Keywords found: {[k for k in order_keywords if k in message_lower]}, Result: {is_order_query}")
        
        return is_order_query

    async def _handle_order_queries(self, session: ChatSession, message_content: str) -> None:
        """Handle order-related queries in the chat session.

        Args:
            session: The chat session
            message_content: The current message content
        """
        import re
        import logging
        logger = logging.getLogger("conversational_commerce")
        
        # Check if order_graph_service is available
        if not self.order_graph_service:
            logger.warning("Order graph service not available, skipping order query handling")
            session.state.add_message("I'm sorry, order processing is not available right now. Please try again later.", is_human=False)
            return
        
        logger.info(f"Starting order query handling for message: '{message_content}'")
        
        # Extract email from the conversation history
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = []
        
        # Check current message and conversation history for emails
        all_messages = [message_content] + [msg.get('content', '') for msg in session.state.messages]
        
        logger.info(f"Checking {len(all_messages)} messages for email addresses")
        
        for i, msg in enumerate(all_messages):
            if isinstance(msg, str):
                found_emails = re.findall(email_pattern, msg)
                if found_emails:
                    logger.info(f"Found emails in message {i}: {found_emails}")
                emails.extend(found_emails)
        
        logger.info(f"Total emails found: {emails}")
         # Fallback to user profile email if no email was found in messages
        profile_email = (session.state.user_profile.email or '').strip() if session.state and session.state.user_profile else ''
        if not emails and profile_email:
            logger.info(f"Using email from user profile: {profile_email}")
            emails = [profile_email]
        
        if not emails:
            # # If no email found, ask for it
            # logger.info("No email found, asking user for email")
            # If no email found anywhere, ask for it
            logger.info("No email found in messages or profile, asking user for email")
            ai_message = "I'd be happy to help you check your order status! Could you please provide your email address?"
            session.state.add_message(ai_message, is_human=False)
            logger.info(f"Added AI message to session: {ai_message}")
            logger.info(f"Session now has {len(session.state.messages)} messages")
            return
        
        # Use the first email found
        user_email = emails[0]
        logger.info(f"Using email: {user_email}")
        
        try:
            logger.info(f"Calling order graph API with question: '{message_content}', email: {user_email}")
            
            # Reuse cache if same email and we recently fetched
            cached = session.state.order_api_cache or {}
            if cached.get("email") == user_email and cached.get("raw_response"):
                logger.info("Using cached order API response for this email")
                order_response = cached["raw_response"]
            else:
                # Try external API first
                order_response = await self._call_external_order_api(
                    question=message_content,
                    user_email=user_email,
                    session_id=session.id
                )
                # Cache raw response and email for reuse within the session
                session.state.order_api_cache = {"email": user_email, "raw_response": order_response}
            
            logger.info(f"Order API response received: {order_response}")
            
            # Extract the final answer
            final_answer = self._extract_final_answer(order_response)
            
            logger.info(f"Extracted final answer: {final_answer}")
            
            if final_answer and final_answer != "No response received from the API." and "error" not in final_answer.lower():
                # # Optionally enrich with product line items from local store (most recent order)
                # try:
                #     orders_for_items = await self.order_graph_service.order_service.get_user_orders(user_email)
                #     if orders_for_items:
                #         most_recent_order = max(orders_for_items, key=lambda x: x.created_at)
                #         if getattr(most_recent_order, "items", None):
                #             items_summary = "; ".join([
                #                 f"{getattr(it, 'name', 'Item')} x{getattr(it, 'quantity', 1)}" for it in most_recent_order.items[:5]
                #             ])
                #             if items_summary:
                #                 final_answer = f"{final_answer}\nItems in most recent order: {items_summary}"
                # except Exception as e:
                #     logger.warning(f"Failed to append items summary: {e}")

                # Add the order response (with items if available) to the chat
                logger.info("Adding order response to chat\n")
                session.state.add_message(final_answer, is_human=False)
            else:
                # Fallback to local order processing
                logger.info("External API failed, trying local order processing")
                local_response = await self._process_order_locally(message_content, user_email)
                session.state.add_message(local_response, is_human=False)
                
        except Exception as e:
            # Error handling
            logger.error(f"Error in order query handling: {e}", exc_info=True)
            # Try local processing as fallback
            try:
                local_response = await self._process_order_locally(message_content, user_email)
                session.state.add_message(local_response, is_human=False)
            except Exception as local_error:
                logger.error(f"Local order processing also failed: {local_error}")
                session.state.add_message(
                    "I'm sorry, I'm having trouble accessing your order information right now. Please try again later or contact customer support.",
                    is_human=False
                )

    async def _call_external_order_api(self, question: str, user_email: str, session_id: str) -> dict:
        """Call the external order API directly.
        
        Args:
            question: The question about orders
            user_email: User's email
            session_id: Session ID
            
        Returns:
            API response as dictionary
        """
        import os
        import json
        import httpx
        import logging
        
        logger = logging.getLogger("conversational_commerce")
        
        try:
            url = os.getenv("ORDER_GRAPH_API_URL", "http://localhost:8000/v1/saleor/orders")
            timeout_seconds = float(os.getenv("ORDER_GRAPH_TIMEOUT", "60"))
            
            # Prepare form data - using the exact format that works
            data = {
                "question": question,
                "additional_details": user_email,  # Pass email as additional_details
                "session_id": session_id,
                "model": "openai_gpt_4o",
                "mode": "graph",
                "database": "mongodb",
                "document_names": json.dumps([])
            }
            
            logger.info(f"Calling external API: {url} with data: {data}")
            
            # Make the request (async, non-blocking)
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, timeout=timeout_seconds)
                response.raise_for_status()
                result = response.json()
            logger.info(f"External API response: {result}")
            return result
            
        except httpx.RequestError as e:
            logger.error(f"Error calling external order API: {e}")
            return {
                "error": f"Failed to call orders API: {str(e)}",
                "final_answer": "Sorry, I couldn't retrieve order information at the moment."
            }
        except Exception as e:
            logger.error(f"Unexpected error calling external API: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "final_answer": "Sorry, an unexpected error occurred while processing your request."
            }

    def _extract_final_answer(self, api_response: dict) -> str:
        """Extract the final answer from the API response.
        
        Args:
            api_response: Response from the external API
            
        Returns:
            Extracted final answer or fallback message
        """
        import logging
        logger = logging.getLogger("conversational_commerce")
        
        try:
            if not api_response or not isinstance(api_response, dict):
                return "No response received from the API."
            
            # Handle the specific API response format you showed
            if "data" in api_response and "answer" in api_response["data"]:
                answer_block = api_response["data"]["answer"]
                
                # Extract the "Final response" part if present
                if "### Final response" in answer_block:
                    final_answer = answer_block.split("### Final response", 1)[1].strip()
                    return final_answer
                else:
                    return answer_block
            
            # Try other possible response formats
            elif "final_answer" in api_response:
                return api_response["final_answer"]
            elif "answer" in api_response:
                return api_response["answer"]
            elif "response" in api_response:
                return api_response["response"]
            else:
                return str(api_response)
                
        except Exception as e:
            logger.error(f"Error extracting final answer: {e}")
            return str(api_response)

    async def _process_order_locally(self, question: str, user_email: str) -> str:
        """Process order questions locally using the order service.
        
        Args:
            question: The question about orders
            user_email: User's email
            
        Returns:
            Formatted response string
        """
        import logging
        logger = logging.getLogger("conversational_commerce")
        
        try:
            logger.info(f"Processing order locally: '{question}' for {user_email}")
            
            # Check if order_graph_service is available
            if not self.order_graph_service:
                return "I'm sorry, order processing is not available right now. Please try again later."
            
            # Get orders from the order service
            orders = await self.order_graph_service.order_service.get_user_orders(user_email)
            
            if not orders:
                return f"I couldn't find any orders for the email {user_email}. Please check your email address or contact customer support if you believe this is an error."
            
            # Generate response based on question type
            question_lower = question.lower()
            
            if "status" in question_lower:
                # Generate status summary
                status_counts = {}
                for order in orders:
                    status = order.status.value
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                status_summary = ", ".join([f"{count} {status}" for status, count in status_counts.items()])
                return f"You have {len(orders)} orders with the following statuses: {status_summary}."
            
            elif "recent" in question_lower or "latest" in question_lower:
                # Show recent orders
                recent_orders = sorted(orders, key=lambda x: x.created_at, reverse=True)[:3]
                order_summary = []
                for order in recent_orders:
                    order_summary.append(f"Order {order.order_id} - {order.status.value} - ${order.total_amount}")
                
                return f"Your recent orders: {'; '.join(order_summary)}"
            
            elif "total" in question_lower or "amount" in question_lower or "spent" in question_lower:
                # Calculate total spent
                total_amount = sum(order.total_amount for order in orders)
                return f"You have spent a total of ${total_amount:.2f} across {len(orders)} orders."
            
            else:
                # General order summary
                total_amount = sum(order.total_amount for order in orders)
                most_recent = max(orders, key=lambda x: x.created_at) if orders else None
                return f"You have {len(orders)} orders with a total value of ${total_amount:.2f}. Your most recent order is {most_recent.order_id if most_recent else 'N/A'} with status {most_recent.status.value if most_recent else 'N/A'}."
                
        except Exception as e:
            logger.error(f"Error in local order processing: {e}", exc_info=True)
            return "I'm sorry, I'm having trouble processing your order information right now."


class GetUserSessionsUseCase:
    """Use case for retrieving all chat sessions for a user."""

    def __init__(self, chat_session_repository: IChatSessionRepository):
        """Initialize the GetUserSessionsUseCase with the provided repository.

        Args:
            chat_session_repository: Chat session repository
        """
        self.chat_session_repository = chat_session_repository

    async def execute(self, user_id: str) -> list[ChatSession]:
        """Execute the use case to retrieve all chat sessions for a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of chat sessions for the user
        """
        return await self.chat_session_repository.get_user_sessions(user_id)


class DeleteChatSessionUseCase:
    """Use case for deleting a chat session."""

    def __init__(self, chat_session_repository: IChatSessionRepository):
        """Initialize the DeleteChatSessionUseCase with the provided repository.

        Args:
            chat_session_repository: Chat session repository
        """
        self.chat_session_repository = chat_session_repository

    async def execute(self, session_id: str) -> bool:
        """Execute the use case to delete a chat session.

        Args:
            session_id: The ID of the chat session to delete

        Returns:
            True if the session was successfully deleted

        Raises:
            ServiceError: If the session is not found
        """
        success = await self.chat_session_repository.delete_session(session_id)
        if not success:
            raise ServiceError(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID {session_id} not found")
        return True
