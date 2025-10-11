import asyncio
import os

from agents import Agent, Runner, function_tool
from config import load_env


@function_tool()
def read_file(file_path: str):
    """
    Reads the file at file_path and returns the full content
    """
    print(f"Tool Call: read_file with path: {file_path}")
    with open(file_path, encoding="utf8") as f:
        return f.read()


@function_tool()
def create_file(file_path: str):
    """
    Creates an empty file at file_path
    """
    print(f"Tool Call: create_file with path: {file_path}")
    with open(file_path, "w", encoding="utf8") as f:
        f.write("")


@function_tool()
def create_directory(directory_path: str):
    """
    Creates a directory at directory_path
    """
    print(f"Tool Call: create_directory with path: {directory_path}")
    os.makedirs(directory_path, exist_ok=True)


async def main():
    load_env()

    agent = Agent(
        name="Assistant",
        tools=[read_file, create_file, create_directory],
        # Not working well with create_file and create_directory
        # model=LitellmModel(model="ollama/llama3.2:3b"),
        instructions="You are a file system assistant.",
    )

    result = await Runner.run(
        agent, "Create a file at current directory called test.txt", max_turns=5
    )
    # print(result.to_input_list())
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
