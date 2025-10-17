import asyncio
import os

import requests
from pydantic import BaseModel
from typing_extensions import TypedDict

from agents import Agent, Runner, SQLiteSession, function_tool
from agents.run_context import RunContextWrapper
from config import with_env

# Example 1:
# Contexts are not passed to the LLM.
# Secure dependency injection.


class AssistantContext(BaseModel):
    weather_api_url: str
    weather_api_key: str


class Location(TypedDict):
    lat: float
    long: float


@function_tool
async def fetch_weather(
    wrapper: RunContextWrapper[AssistantContext],
    location: Location,
) -> str:
    base_url = wrapper.context.weather_api_url
    params = {
        "lat": location["lat"],
        "lon": location["long"],
        "appid": wrapper.context.weather_api_key,
        "units": "metric",
    }

    # Run the synchronous requests call in a thread pool
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, base_url, params)
    response.raise_for_status()

    data = response.json()
    weather_desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]

    return f"""
    Weather: {weather_desc.title()},
    Temperature: {temp}°C (feels like {feels_like}°C),
    Humidity: {humidity}%
    """


agent = Agent(
    name="Assistant",
    tools=[fetch_weather],
)


@with_env
async def main():
    session = SQLiteSession("weather", "weather.sql")

    ctx = AssistantContext(
        weather_api_url="https://api.openweathermap.org/data/2.5/weather",
        weather_api_key=os.environ.get("OPENWEATHER_API_KEY"),
    )

    result = await Runner.run(
        agent,
        """I'm planning a trip to Israel, what is the weather in Tel Aviv,
        Jerusalem, Haifa and Eilat today?""",
        session=session,
        context=ctx,
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
