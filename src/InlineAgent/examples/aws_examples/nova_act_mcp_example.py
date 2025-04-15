import os
from mcp import StdioServerParameters

from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

# Step 1: Define MCP stdio parameters
NOVA_ACT_API_KEY = os.getenv("NOVA_ACT_API_KEY")

server_params = StdioServerParameters(
    command="python",
    args=[
        "nova_act_server.py",
    ],
    env={"NOVA_ACT_API_KEY": NOVA_ACT_API_KEY},
)


async def main():
    # Step 2: Create MCP Client
    nova_act_mcp_client = await MCPStdio.create(server_params=server_params)

    try:
        # Step 3: Define an action group
        nova_act_action_group = ActionGroup(
            name="NovaActGroup",
            description="Uses Amazon Nova Act to accomplish tasks",
            mcp_clients=[nova_act_mcp_client],
        )

        # Step 4: Invoke agent
        await InlineAgent(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            # Step 4.2: Concise instruction
            instruction="""You are a friendly assistant that is responsible for resolving user queries. """,
            # Step 4.3: Provide the agent name and action group
            agent_name="amazon_agent",
            action_groups=[nova_act_action_group],
        ).invoke(
            input_text="Find the first backpack on amazon.com, use headless mode."
        )

    finally:

        await nova_act_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
