import asyncio
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from config import with_env


class BlogPostIdea(BaseModel):
    title: str = Field(..., title="Title", description="The title of the blog post")
    main_concepts: list[str] = Field(
        ..., title="Main Concepts", description="Main concepts for the post"
    )


@with_env
async def main(general_topic: str):
    # Load instructions from file
    script_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(script_dir))
    template = env.get_template("instructions.md")

    # Researcher Agent
    researcher_agent = Agent(
        name="MarketResearcher",
        model=LitellmModel(model="openrouter/anthropic/claude-3-5-sonnet"),
        # Removed output_type since claude doesn't support structured
        # json outputs via OpenRouter
        # output_type=list[BlogPostIdea],
        instructions=template.render(general_topic=general_topic),
    )

    result = await Runner.run(
        researcher_agent,
        "Create 5 blog posts subject lines and main concept",
    )
    print(result.raw_responses)


if __name__ == "__main__":
    asyncio.run(main("weather"))
