# Old Ecommerce Conversational AI: Backend Chat API Documentation

## Overview

The chat API in this application is a sophisticated conversational AI system designed to provide personalized product recommendations and activity planning for users. It leverages a multi-agent architecture orchestrated through a workflow graph to process user queries and generate contextually relevant responses.

## API Endpoint Structure

The main endpoint is exposed through FastAPI:

```python
@chat_router.post("/chat/chat")
async def chat(query: ChatQuery):
    result = chat_entity_manager.create_adventure_advisor(query)

    # Structure the response
    response = {
        "message": result["message"],
        "product_recommendations": result.get("product_recommendations", None)
    }

    return response
```

This endpoint accepts a `ChatQuery` object containing the user's question and returns a structured response with a message and optional product recommendations.

## Core Components

### 1. ChatEntityManager

The ChatEntityManager class is responsible for:

- Creating and orchestrating the agent workflow
- Managing the state throughout the conversation
- Structuring the final response

It uses LangGraph's `StateGraph` to create a directed workflow of specialized agents:

```python
workflow = StateGraph(AgentState)
workflow.add_node("master", self.agent.create_master_agent())
workflow.add_node("gear_agent", self.agent.create_gear_agent())
workflow.add_node("activity_planner", self.agent.trip_planner_agent())
```

### 2. Agent System

The system implements multiple specialized agents:

#### Master Agent

- Acts as the entry point for all queries
- Analyzes the user's request to determine intent
- Routes the query to the appropriate specialized agent

#### Gear Agent

- Handles product recommendation requests
- Converts natural language queries into SQL queries
- Retrieves products from the database based on user preferences
- Filters out products the user has already purchased
- Formats recommendations for the frontend

#### Activity Planner Agent

- Processes trip and activity planning requests
- Generates detailed activity recommendations

#### Weather Agent (auxiliary)

- Extracts location and date information from queries
- Retrieves weather data for the specified location and date
- Supports the activity planner with contextual weather information

## Workflow Process

1. **Query Intake**: The user's query is received through the `/chat/chat` endpoint
2. **Initial State Creation**: An `AgentState` object is created with the user's message
3. **Master Agent Processing**: The master agent analyzes the query to determine its type
4. **Conditional Routing**: Based on the query type, the workflow routes to either:
   - Gear Agent (for product recommendations)
   - Activity Planner (for trip planning)
5. **Specialized Processing**: The selected agent processes the query using:
   - LLM-based natural language understanding
   - Database queries for product information
   - User preference analysis
6. **Response Generation**: The agent generates a structured response
7. **Response Formatting**: The response is formatted with:
   - A natural language message
   - Structured product recommendations (when applicable)

## Technical Implementation Details

### State Management

The system uses a shared state object (`AgentState`) that contains:

- Message history
- Next agent to process
- Activity details
- Product recommendations
- Weather information
- Query type classification
- Extracted information

### LLM Integration

The system uses OpenAI's models (primarily GPT-4) through LangChain to:

- Parse user queries
- Extract structured information
- Generate natural language responses
- Convert natural language to SQL queries

### Database Integration

The Gear Agent connects to a PostgreSQL database to:

- Retrieve product information based on generated SQL queries
- Filter products based on user purchase history
- Apply user preferences to product recommendations

### Error Handling

The system implements comprehensive error handling:

- Graceful degradation when services fail
- Informative error messages
- Logging for debugging and monitoring

## Product Recommendation System

### How Products Are Recommended

Products are recommended through the Gear Agent, which follows these steps:

1. **Query Analysis**: When a user asks about products or gear, the Master Agent identifies the query as product-related and routes it to the Gear Agent.

2. **Natural Language to SQL Conversion**: The Gear Agent converts the natural language query into a structured SQL query using the `get_sql_query()` method with a specialized prompt.

3. **Database Retrieval**: The system executes the SQL query against the product database to fetch matching products.

4. **Filtering Process**:

   - Products the user has already purchased are filtered out
   - The system checks the user's purchase history to avoid recommending items they already own

5. **User Preference Application**:

   - The system retrieves the user's preferences from the database
   - It applies these preferences to rank and filter the products using the `get_preference_based_recommendations()` method
   - This creates a personalized recommendation list tailored to the user

6. **Response Formatting**: The recommendations are formatted into a structured response with:
   - Product details (name, price, category, etc.)
   - Review scores
   - Images
   - Relevance information

### When Products Are Recommended

Products are recommended in these scenarios:

1. **Direct Product Queries**: When users explicitly ask for product recommendations (e.g., "What hiking boots should I buy?")

2. **Gear-Related Keywords**: When the Master Agent detects product-related keywords in the query such as "product_only", "product recommendations", or "gear"

3. **Activity Context**: When discussing activities that require specific gear (the query is routed to the Gear Agent)

4. **Query Classification**: The Master Agent analyzes each query and sets `state["query_type"] = "product"` when it determines a product recommendation is needed

The recommendation process is triggered by the routing decision in the Master Agent:

```python
if any(keyword in response_text for keyword in ["product_only", "product recommendations", "gear"]):
    logger.info("✨ Master Agent routing to Gear Agent")
    state["query_type"] = "product"
    state["next_agent"] = "gear_agent"
```

This intelligent routing ensures that product recommendations are provided when they're most relevant to the user's needs, creating a seamless conversational shopping experience.

## Conclusion

The chat API represents a sophisticated multi-agent system that combines natural language processing, database operations, and conditional workflows to provide personalized recommendations. The architecture allows for easy extension with additional specialized agents and demonstrates effective use of modern AI orchestration techniques.
