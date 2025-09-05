"""Simple test endpoint to verify CopilotKit integration."""

import logging
from fastapi import APIRouter
from copilotkit import CopilotKitSDK, LangGraphAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint

logger = logging.getLogger("test_copilotkit")

router = APIRouter()

# Simple test agent that just echoes back messages
class SimpleEchoAgent:
    async def ainvoke(self, state, config=None):
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = getattr(last_message, 'content', str(last_message))
            from langchain_core.messages import AIMessage
            return {
                "messages": messages + [AIMessage(content=f"Echo: {content}")]
            }
        return state
    
    def invoke(self, state, config=None):
        import asyncio
        return asyncio.run(self.ainvoke(state, config))

def create_test_app():
    """Create a test FastAPI app with CopilotKit."""
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # Initialize CopilotKit SDK with simple echo agent
    sdk = CopilotKitSDK(
        agents=[
            LangGraphAgent(
                name="test_echo_agent",
                description="Simple echo agent for testing",
                graph=SimpleEchoAgent(),
            )
        ],
    )

    # Add CopilotKit endpoint
    add_fastapi_endpoint(app, sdk, "/test_copilotkit")
    
    return app

# Export the test app
test_app = create_test_app()
