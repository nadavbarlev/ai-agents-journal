import asyncio
from dataclasses import dataclass
from typing import Literal

from langsmith.wrappers import OpenAIAgentsTracingProcessor

from agents import Agent, Runner, SQLiteSession, set_trace_processors, trace
from config import with_env

"""
This example shows the LLM as a judge pattern, to deal with the inconsistency of
language models. The first agent generates an outline for a story. The second agent
judges the outline and provides feedback. We loop until the judge is satisfied
with the outline.
"""

story_generator_agent = Agent(
    name="story_generator",
    instructions=(
        "You generate a very short story outline based on the user's input."
        "If there is any feedback provided, use it to improve the outline."
    ),
)


@dataclass
class EvaluationFeedback:
    score: Literal["pass", "needs_improvement", "fail"]
    # In structured output, it is always a good idea to add a free text field so that
    # the model can express itself (yes it helps to get a better result).
    feedback: str


story_evaluator_agent = Agent(
    name="story_evaluator",
    instructions="""
        You evaluate a story outline and decide if it's good enough.
        If it's not good enough, you provide feedback on what needs to be improved.
        Never give it a pass on the first try. After 5 attempts, you can give it a pass
        if the story outline is good enough - do not go for perfection"
    """,
    output_type=EvaluationFeedback,
)


@with_env
async def main() -> None:
    set_trace_processors([OpenAIAgentsTracingProcessor()])

    story_generator_session = SQLiteSession("generator")
    story_evaluator_session = SQLiteSession("evaluator")

    msg = input("what kind of story would you like to hear? ")

    max_turns = 7
    latest_story: str | None = None
    result: EvaluationFeedback | None = None

    # We'll run the entire workflow in a single trace
    with trace("Day-18: LLM as a judge"):
        for turn in range(max_turns):
            story_generator_result = await Runner.run(
                story_generator_agent,
                msg,
                session=story_generator_session,
                max_turns=1,  # Gets 1 turn to respond (no tool loops)
            )

            latest_story = story_generator_result.final_output

            print("story was generated successfully")

            story_evaluator_result = await Runner.run(
                story_evaluator_agent,
                latest_story,
                session=story_evaluator_session,
                max_turns=1,
            )
            result = story_evaluator_result.final_output

            print(f"story evaluator score: {result.score}")

            if result.score == "pass":
                print("story is good enough, exiting.")
                break

            print("re-running generator with feedback")
            await story_generator_session.add_items(
                [
                    {"role": "user", "content": f"Feedback: {result.feedback}"},
                ]
            )

    # Check if we exited due to max turns or success
    if result is None or result.score != "pass":
        print(
            f"""We couldn't create a good story after {max_turns} attempts.
                The final story (not approved): {latest_story}"""
        )
    else:
        print(f"The final story: {latest_story}")


if __name__ == "__main__":
    asyncio.run(main())
