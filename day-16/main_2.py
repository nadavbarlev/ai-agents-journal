import asyncio

from pydantic import BaseModel

from agents import Agent, RunContextWrapper, Runner, SQLiteSession, function_tool
from config import with_env

# Example 2:
# Context can be used to pass information between tools or
# to store information that tools can "edit".


class UserContext(BaseModel):
    name: str | None
    favorite_programming_language: str | None


@function_tool
async def set_name(
    wrapper: RunContextWrapper[UserContext],
    name: str,
) -> str:
    """save user name"""
    wrapper.context.name = name
    return f"user name set to {name}"


@function_tool
async def set_favorite_programming_language(
    wrapper: RunContextWrapper[UserContext],
    favorite_programming_language: str,
) -> str:
    """save favorite programming language"""
    wrapper.context.favorite_programming_language = favorite_programming_language
    return f"favorite programming language set to {favorite_programming_language}"


@with_env
async def main():
    session = SQLiteSession("info")  # in-memory conversation memory
    ctx = UserContext(name=None, favorite_programming_language=None)

    agent = Agent(
        name="Assistant",
        instructions="""You are a programming teacher and you want to welcome students
        to your class. Find out what their name and favorite programming languages are
        and save the information using the provided tools. Be gentle with the students
        and ask just one question at a time.
        """,
        tools=[set_name, set_favorite_programming_language],
    )

    next_message = "start the conversation with the student."
    while True:
        result = await Runner.run(
            agent,
            next_message,
            session=session,
            context=ctx,
        )

        print(result.to_input_list)
        print(result.final_output)

        if ctx.name is not None and ctx.favorite_programming_language is not None:
            break

        next_message = input()

    print(ctx)


if __name__ == "__main__":
    asyncio.run(main())
