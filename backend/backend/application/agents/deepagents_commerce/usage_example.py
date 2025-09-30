"""
Minimal Usage Example for Deep Agent Integration
Shows how to integrate the deep agent with your existing chat session system.
"""

# Example of how to use the deep agent workflow in your existing ProcessChatMessageUseCase

# 1. Use the existing WorkflowFactory to get the deep agent workflow
#    In your ProcessChatMessageUseCase.execute, replace the workflow selection:
#    
#    # Instead of:
#    # workflow = self.workflow_factory.get_workflow_for_user(session.user_id)
#    
#    # Use:
#    workflow = self.workflow_factory.get_deep_agent_commerce_workflow()  # Get singleton instance
#    session.state = await workflow.run(session.state)

# 2. That's it! The deep agent will now handle the conversation with:
#    - 4 specialized subagents (Discovery, Catalog, Bundler, Critic)
#    - Real service integration (ProductService, OrderGraphService, etc.)
#    - Advanced memory and personalization
#    - Intelligent product bundling
#    - Singleton pattern for efficient resource usage

print("Deep Agent Integration - Minimal Setup Complete!")
print("Just use workflow_factory.get_deep_agent_commerce_workflow() to get the singleton instance")
