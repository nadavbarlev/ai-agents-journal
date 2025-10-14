import asyncio
import os
import sys
from pathlib import Path

from agents import (
    Agent,
    FunctionToolResult,
    Runner,
    SQLiteSession,
    ToolsToFinalOutputResult,
    function_tool,
)
from config import with_env


@function_tool
async def list_directory_files(directory_path: str = ".") -> str:
    """List files and directories in a given directory.

    Args:
        directory_path: Directory path (default: current directory)

    Returns:
        List of files and directories
    """

    try:
        path = Path(directory_path)
    except Exception as e:
        return f"error: invalid directory path: {repr(e)}"

    if not path.exists():
        return f"error: directory {directory_path} does not exist"

    if not path.is_dir():
        return f"error: {directory_path} is not a directory"

    items = []
    for item in sorted(path.iterdir()):
        if item.is_dir():
            items.append(f"directory: {item.name}/")

    if not items:
        return f"directory {directory_path} is empty"

    return f"contents of directory {path.absolute()}:\n" + "\n".join(items)


@function_tool
async def read_text_file(file_path: str) -> str:
    """Read the content of a text file.

    Args:
        file_path: Path to the file to read

    Returns:
        File content
    """
    try:
        path = Path(file_path)
    except Exception as e:
        return f"error: invalid file path: {repr(e)}"

    if not path.exists():
        return f"error: file {file_path} does not exist"

    if not path.is_file():
        return f"error: {file_path} is not a file"

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"error: reading file: {repr(e)}"

    if not content.strip():
        return f"error: file {file_path} is empty"

    return f"content of file {file_path}:\n\n{content}"


@function_tool
async def change_directory(directory_path: str) -> str:
    """Change to another directory.

    Args:
        directory_path: Path to the new directory

    Returns:
        Message about the directory change
    """
    try:
        path = Path(directory_path)
    except Exception as e:
        return f"error: invalid directory path: {repr(e)}"

    if not path.exists():
        return f"error: directory {directory_path} does not exist"

    if not path.is_dir():
        return f"error: {directory_path} is not a directory"

    os.chdir(str(path.absolute()))
    current_dir = Path.cwd()
    return f"changed to directory: {current_dir}"


def files_tool_use_behavior(
    context, tool_results: list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    read_attempts = sum(1 for r in tool_results if r.tool.name == "read_text_file")
    if read_attempts >= 5:
        return ToolsToFinalOutputResult(
            is_final_output=True,
            final_output="search completed after checking multiple files.",
        )

    error_count = sum(
        1
        for r in tool_results
        if isinstance(r.output, str) and r.output.startswith("error:")
    )
    if error_count >= 3:
        return ToolsToFinalOutputResult(
            is_final_output=True,
            final_output="search stopped due to too many errors.",
        )

    # Continue searching
    return ToolsToFinalOutputResult(is_final_output=False)


@with_env
async def main():
    if len(sys.argv) > 1:
        search_text = " ".join(sys.argv[1:])
    else:
        raise ValueError("no search text provided")

    print(f"search text: {search_text}")

    instructions = """
    You are a smart file manager assistant.
    You can help users navigate the file system, read files, and change
    between directories. Always be helpful and friendly in your responses."""

    agent = Agent(
        name="File Manager",
        instructions=instructions,
        tools=[list_directory_files, read_text_file, change_directory],
        tool_use_behavior=files_tool_use_behavior,
    )

    search_query = f"""
    Search for a file that contains the text '{search_text}'.
    First, list the files in the current directory, then read files to find one
    containing this text. If needed, navigate to subdirectories to search thoroughly.
    When you find a file containing the text, report which file it is and show the
    relevant content.
    """
    session = SQLiteSession("files", "files.sql")

    result = await Runner.run(
        agent,
        search_query,
        session=session,
        max_turns=5,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
