import asyncio

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from config import with_env


@with_env
async def main():
    # OpenAI Model
    # agent = Agent(
    #     name="Assistant",
    #     model="gpt-4.1-nano",
    #     instructions="You only respond in haikus.",
    # )

    # Non-OpenAI Model
    agent = Agent(
        name="Assistant",
        model=LitellmModel(model="ollama/llama3.2:3b"),
        instructions="You only respond in haikus.",
    )

    result = await Runner.run(agent, "Tell me about recursion in programming.")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
