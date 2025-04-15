import os
import asyncio
import logging

from mcp import StdioServerParameters

from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

# Step 1: Define MCP stdio parameters
docs_server_params = StdioServerParameters(
    command="uvx",
    args=[
        "awslabs.aws-documentation-mcp-server@latest",
    ]
)

diag_server_params = StdioServerParameters(
    command="uvx",
    args=[
        "awslabs.aws-diagram-mcp-server",
    ]
)

# Custom cleanup to handle the task cancellation issue
async def safe_cleanup(client, timeout=2.0):
    """Safely cleanup a client with a timeout"""
    try:
        # Create a task for the cleanup operation
        cleanup_task = asyncio.create_task(client.cleanup())
        
        # Wait for the task to complete with a timeout
        try:
            await asyncio.wait_for(cleanup_task, timeout)
            print(f"Client cleanup completed successfully")
        except asyncio.TimeoutError:
            print(f"Client cleanup timed out, but continuing")
            # We don't cancel the task here to avoid further issues
    except Exception as e:
        print(f"Ignoring cleanup error: {e.__class__.__name__}")


async def main():
    # Step 2: Create MCP Client
    aws_docs_mcp_client = await MCPStdio.create(server_params=docs_server_params)
    aws_diag_mcp_client = await MCPStdio.create(server_params=diag_server_params)
    try:
        # Step 3: Define an action group
        aws_docs_group = ActionGroup(
            name="AWSDocsGroup",
            description="Gets AWS Documentation",
            mcp_clients=[aws_docs_mcp_client, aws_diag_mcp_client],
        )

        # Step 4: Invoke agent
        await InlineAgent(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            # Step 4.2: Concise instruction
            instruction="""You are an expert AWS Certified Solutions Architect. Your role is to help customers understand best practices on building on AWS. You can querying the AWS Documentation and generate diagrams. Make sure to tell the customer the full file path of the diagram.""",
            # Step 4.3: Provide the agent name and action group
            agent_name="amazon_agent",
            action_groups=[aws_docs_group],
        ).invoke(
            input_text="Get the documentation for AWS Lambda then create a diagram of a website that uses AWS Lambda for a static website hosted on S3"
        )

    finally:
        print("Cleaning up clients")
        
        # Use our custom safe cleanup
        await safe_cleanup(aws_docs_mcp_client)
        await safe_cleanup(aws_diag_mcp_client)
        
        # Force exit to avoid any lingering tasks causing issues
        print("Cleanup completed, exiting")

if __name__ == "__main__":
    # Configure asyncio to hide error messages
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    
    # Run the main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user, exiting")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Force exit to ensure no hanging processes
        os._exit(0)
