import asyncio
from uuid import uuid4

from agents import (
    Agent,
    FunctionToolResult,
    Runner,
    SQLiteSession,
    ToolsToFinalOutputResult,
    function_tool,
)
from config import with_env

boxes = [
    {"id": str(uuid4()), "has_treasure": False},
    {"id": str(uuid4()), "has_treasure": True},
    {"id": str(uuid4()), "has_treasure": False},
]


@function_tool
async def open_box(id: str) -> bool:
    """Open a box and search for the treasure inside. Returns True if found"""
    return next(b["has_treasure"] for b in boxes if b["id"] == id)


@function_tool
async def get_box_ids() -> list[str]:
    return [b["id"] for b in boxes]


# Call each time a tool is used with the context and the tool results
def custom_tool_use_behavior(
    context, tool_results: list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    print(context)

    # Stop the agent after one time the open_box tool is used
    for result in tool_results:
        if result.tool.name == "open_box":
            return ToolsToFinalOutputResult(
                is_final_output=True, final_output=result.output
            )
    return ToolsToFinalOutputResult(is_final_output=False)


# agent = Agent(
#     name="Assistant",
#     tools=[open_box, get_box_ids],
# )

agent = Agent(
    name="Assistant",
    tools=[open_box, get_box_ids],
    tool_use_behavior=custom_tool_use_behavior,
)


@with_env
async def main():
    session = SQLiteSession("boxes", "boxes.sql")

    # result = await Runner.run(
    #     agent,
    #     """
    #     Let's play a game. You are given 3 boxes and you need to find the treasure
    #     hidden in one of them. You can open any box you want to look inside.
    #     Use open_box tool to open boxes and find the treasure.
    #     Try to find it by opening the miniumum number of boxes.
    #     """,
    #     session=session,
    #     max_turns=5,
    # )

    result = await Runner.run(
        agent,
        """
        Let's play a game. You are given 3 boxes and you need to find the treasure
        hidden in one of them. You can open any box you want to look inside.
        Use open_box tool to open boxes and find the treasure.
        Try to find it by opening the miniumum number of boxes.
        """,
        session=session,
        max_turns=5,
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
