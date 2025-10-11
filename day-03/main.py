import asyncio

from pydantic import BaseModel, Field

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from config import with_env


class BlogPostIdea(BaseModel):
    title: str = Field(..., title="Title", description="The title of the blog post")
    main_concepts: list[str] = Field(
        ..., title="Main Concepts", description="Main concepts for the post"
    )


class RatedBlogPostIdea(BaseModel):
    blog_post: BlogPostIdea = Field(
        ..., title="Blog Post", description="The selected blog post idea"
    )
    rating: float = Field(
        ..., title="Rating", description="Rating from 1-10 for the blog post idea"
    )
    reasoning: str = Field(
        ...,
        title="Reasoning",
        description="Explanation for why this idea was selected and rated",
    )


@with_env
async def main(general_topic: str):
    # Market Research Agent
    market_research_agent = Agent(
        name="MarketResearcher",
        model="gpt-4.1-nano",
        output_type=list[BlogPostIdea],
        instructions="""
        You are a market researcher and your job is to suggest cool ideas for
        blog posts. I will send you ideas and you will help me turn them into
        engaging posts, Or I will send you topics and you will help to focus me
        on the best viral ideas in these niches.
        """,
    )

    result = await Runner.run(
        market_research_agent,
        f"Create 5 blog posts subject lines and main concept for: {general_topic}",
    )

    # Rating Agent
    rating_agent = Agent(
        name="RatingAgent",
        model=LitellmModel(model="ollama/llama3.2:3b"),
        output_type=RatedBlogPostIdea,
        instructions="""
        You are a rating agent and your job is to evaluate blog post ideas and select
        the best one. Rate each idea from 1-10 based on:
        - Viral potential and engagement
        - Uniqueness and originality
        - Practical value for readers
        - SEO potential and searchability
        Select the highest-rated idea and provide your reasoning for the rating.
        """,
    )

    rated_result = await Runner.run(
        rating_agent,
        f"Rate and select the best blog post idea from these options: {
            result.final_output
        }",
    )

    # Writer Agent
    writer_agent = Agent(
        name="Writer",
        model=LitellmModel(model="ollama/llama3.2:3b"),
        instructions="""
        You are a copywriter creating engaging and viral blog posts.
        """,
    )
    post = await Runner.run(
        writer_agent,
        f"Create a blog post from the following data: {rated_result.final_output}",
    )
    print(post.final_output)


if __name__ == "__main__":
    asyncio.run(main("workouts"))
