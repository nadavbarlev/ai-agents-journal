import asyncio

from agents import Agent, Runner, SQLiteSession
from config import with_env


@with_env
async def main():
    # Chat Without Session
    # agent = Agent(
    #     name="Assistant",
    #     instructions="Reply very concisely.",
    # )
    # message = input("> ")
    # result = await Runner.run(agent, message)
    # print(result.final_output)

    # while True:
    #     message_history = result.to_input_list()
    #     print(f"Messages: {message_history}")

    #     message = input("> ")
    #     result = await Runner.run(
    #         agent, message_history + [{"role": "user", "content": message}]
    #     )
    #     print(result.final_output)

    # Chat With Session
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely.",
    )

    session = SQLiteSession("conversation_day04")

    while True:
        user_message = input("> ")
        response = await Runner.run(agent, user_message, session=session)
        print(response.final_output)


if __name__ == "__main__":
    asyncio.run(main())
