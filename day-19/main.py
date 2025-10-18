import asyncio

from langsmith.wrappers import OpenAIAgentsTracingProcessor

from agents import Agent, Runner, set_trace_processors, trace
from config import with_env

"""
This example shows the parallelization pattern. We run the agent three times
in parallel, and pick the best result.

Guardrails work behind the scenes via parallel agents - one processes user input
while a shadow guardrail agent validates requests and stops the main agent on problems.
"""

spanish_agent = Agent(
    name="spanish_agent",
    instructions="You translate the user's message to Spanish",
)

translation_picker = Agent(
    name="translation_picker",
    instructions="You pick the best Spanish translation from the given options.",
)


@with_env
async def main():
    set_trace_processors([OpenAIAgentsTracingProcessor()])

    msg = """
    I was a ghost, I was alone
    Given the throne, I didn't know how to believe
    I was the queen that I'm meant to be
    I lived two lives, tried to play both sides
    But I couldn't find my own place
    Called a problem child 'cause I got too wild
    But now that's how I'm getting paid on stage
    """

    # Ensure the entire workflow is a single trace
    with trace("Day-19: Parallel Translation"):
        results = await asyncio.gather(
            Runner.run(
                spanish_agent,
                msg,
            ),
            Runner.run(
                spanish_agent,
                msg,
            ),
            Runner.run(
                spanish_agent,
                msg,
            ),
        )

        outputs = [result.final_output for result in results]

        translations = "\n\n".join(outputs)
        print(f"Translations:\n\n{translations}")

        best_translation = await Runner.run(
            translation_picker,
            f"""
            Input:\n{msg}
            \n\n
            Translations:\n{translations}
            """,
        )

    print(best_translation.final_output)


if __name__ == "__main__":
    asyncio.run(main())
