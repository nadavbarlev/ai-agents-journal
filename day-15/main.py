import asyncio

from agents import Agent, Runner
from agents.mcp import MCPServer, MCPServerStreamableHttp
from agents.model_settings import ModelSettings
from config import with_env


async def run(mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the questions.",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),  # Must use the MCP tool
    )

    result = await Runner.run(
        agent,
        "Summarize the top stories from CNBC today. URL is: https://www.cnbc.com/world/?region=world",
    )

    print(result.to_input_list())
    print(result.final_output)


@with_env
async def main():
    async with MCPServerStreamableHttp(
        name="Streamable HTTP Python Server",
        params={
            "url": "https://remote.mcpservers.org/fetch/mcp",
        },
    ) as server:
        await run(server)


if __name__ == "__main__":
    asyncio.run(main())
