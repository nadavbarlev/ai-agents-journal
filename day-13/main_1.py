import asyncio
from typing import Literal

from pydantic import BaseModel, Field

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from config import with_env


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]


class NoEvent(BaseModel):
    no_event: Literal[True] = True
    reason: str = Field(
        ...,
        min_length=5,
        description="Why the text contains no actionable calendar event.",
    )


ExtractEventResult = CalendarEvent | NoEvent

agent = Agent(
    name="Calendar extractor",
    # Sometimes works, but with inputs like `Hello` it creates irrelevant
    # calendar events - so the instructions are important.
    model=LitellmModel(model="ollama/llama3.2:3b"),
    # Does not work with an output_type of OpenAI.
    # model=LitellmModel(model="openrouter/anthropic/claude-3-5-sonnet"),
    instructions="""Extract calendar events from text.
    1) If (and only if) the text clearly specifies an event-like intent (meeting, call,
    appointment, trip, deadline, holiday) AND includes at least one of:
    • a date (absolute like “Oct 14, 2025” or relative resolvable like “tomorrow”), or
    • a time range/timepoint (e.g., “09:00–10:00”, “at 3pm”), or
    • an all-day indicator (“on Friday”, “this Monday” for an all-day event),
    then RETURN a CalendarEvent.
    2) Otherwise, RETURN NoEvent with a brief reason (e.g., “Greeting only”,
    “Missing date/time”, “Ambiguous request”).
    """,
    output_type=ExtractEventResult,
)


@with_env
async def main():
    # input = "Hello"
    input = "We're having a party this Saturday night, 9:00pm with Mark and Dana"
    result = await Runner.run(agent, input)
    print(result.final_output.__class__)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
