import asyncio

from agents import Agent, Runner, SQLiteSession
from config import with_env

# When to Use Handoffs:

# 1. Model Selection for Complexity - Route simple requests to cheaper models
# (like GPT-4.1-mini) and complex requests to more powerful models to
# optimize cost vs. performance.

# 2. Specialized Instructions - Hand off to agents with different instruction sets
# when certain request types would benefit from specialized handling.

# 3. Context Control - Transfer requests to other models with limited or no
# conversation history when you need cleaner context for better processing.

french_agent = Agent(
    name="French Translator",
    instructions="Translate everything to french",
)

spanish_agent = Agent(
    name="Spanish Translator",
    instructions="Translate everything to Spanish",
)

triage_agent = Agent(
    name="Triage agent",
    handoffs=[french_agent, spanish_agent],
)


@with_env
async def main():
    session = SQLiteSession("handoffs", "handoffs.sql")
    result = await Runner.run(
        triage_agent,
        "translate to French: 'hello world'",
        session=session,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
