import asyncio
import os

from tavily import AsyncTavilyClient

from agents import Agent, Runner, WebSearchTool, function_tool
from config import with_env

# AGENT-SDK EXPENSIVE SOLUTION:

agent = Agent(
    name="Assistant",
    tools=[
        WebSearchTool(),
    ],
)


@function_tool
async def tavily_search(query: str) -> str:
    """Search the web using Tavily API.

    Args:
        query: The search query string

    Returns:
        Formatted search results with titles, URLs, and content snippets
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set"

    client = AsyncTavilyClient(api_key=api_key)
    response = await client.search(query, max_results=5)

    if not response or "results" not in response:
        return "No results found"

    return response["results"]


@with_env
async def main():
    result = await Runner.run(
        agent,
        """Which coffee shop should I go to, taking into account the weather
        today in Tel-Aviv? Also, please provide the address of the coffee shop.""",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
