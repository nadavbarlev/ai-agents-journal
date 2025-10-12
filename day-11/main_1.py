import asyncio

from agents import Agent, CodeInterpreterTool, Runner
from config import with_env

# NOT SECURE SOLUTION:

# @function_tool
# async def run_python(code: str) -> str:
#     """Run provided python code and return the value of "result"
#     global variable as string.

#     Args:
#         code: python code to execute

#     Example input to return the value of 5 + 7:
#         x = 5
#         y = 7
#         result = x + y
#     """
#     print(f"Running Code: \n\n{code}")
#     ns = {}
#     exec(code, ns)
#     print(f"Result = {ns['result']}")
#     return str(ns["result"])


# agent = Agent(
#     name="Assistant",
#     tools=[run_python],
# )

# SECURE SOLUTION:

agent = Agent(
    name="Assistant",
    tools=[
        CodeInterpreterTool(
            tool_config={"type": "code_interpreter", "container": {"type": "auto"}}
        )
    ],
)


@with_env
async def main():
    result = await Runner.run(
        agent, "What is the current os.name? use Python to find out"
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
