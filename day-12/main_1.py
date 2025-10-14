import asyncio
import os

import requests
from typing_extensions import TypedDict

from agents import Agent, Runner, SQLiteSession, function_tool
from config import with_env


class Location(TypedDict):
    lat: float
    long: float


# I can ask the agent to pass certain values but the real control
# over which values will be passed is limited
@function_tool
async def fetch_weather(location: Location) -> str:
    print(f"fetching weather for {location}...")

    weather_api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not weather_api_key:
        return "Error: OpenWeather API key not found in environment variables"

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": location["lat"],
        "lon": location["long"],
        "appid": weather_api_key,
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

    result = await Runner.run(
        agent,
        """I'm planning a trip to Israel, what is the weather in Tel Aviv,
        Jerusalem, Haifa and Eilat today?""",
        session=session,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())


# SESSION MESSAGES:

# 5|weather|{"content": "I'm planning a trip to Israel, what is the weather in Tel Aviv, Jerusalem, Haifa and Eilat today?", "role": "user"}|2025-08-14 09:59:42  # noqa: E501
# 6|weather|{"arguments": "{\"location\": {\"lat\": 32.0853, \"long\": 34.7818}}", "call_id": "call_la2QHswRUH0Xa80wZNLQ6dOv", "name": "fetch_weather", "type": "function_call", "id": "__fake_id__"}|2025-08-14 09:59:42  # noqa: E501
# 7|weather|{"arguments": "{\"location\": {\"lat\": 31.7683, \"long\": 35.2137}}", "call_id": "call_AEGdktcxYfR2MzGS7BzhA9AY", "name": "fetch_weather", "type": "function_call", "id": "__fake_id__"}|2025-08-14 09:59:42  # noqa: E501
# 8|weather|{"arguments": "{\"location\": {\"lat\": 32.794, \"long\": 34.9896}}", "call_id": "call_CFb2TkCz6M6eL19aT7c69Zae", "name": "fetch_weather", "type": "function_call", "id": "__fake_id__"}|2025-08-14 09:59:42  # noqa: E501
# 9|weather|{"arguments": "{\"location\": {\"lat\": 29.5577, \"long\": 34.9519}}", "call_id": "call_DWgN1qFAru8ScClVHj1jgqIz", "name": "fetch_weather", "type": "function_call", "id": "__fake_id__"}|2025-08-14 09:59:42  # noqa: E501
# 10|weather|{"call_id": "call_la2QHswRUH0Xa80wZNLQ6dOv", "output": "Weather: Clear Sky, Temperature: 36.9\u00b0C (feels like 40.23\u00b0C), Humidity: 38%", "type": "function_call_output"}|2025-08-14 09:59:42  # noqa: E501
# 11|weather|{"call_id": "call_AEGdktcxYfR2MzGS7BzhA9AY", "output": "Weather: Clear Sky, Temperature: 38.34\u00b0C (feels like 42.39\u00b0C), Humidity: 36%", "type": "function_call_output"}|2025-08-14 09:59:42  # noqa: E501
# 12|weather|{"call_id": "call_CFb2TkCz6M6eL19aT7c69Zae", "output": "Weather: Clear Sky, Temperature: 33.39\u00b0C (feels like 34.41\u00b0C), Humidity: 40%", "type": "function_call_output"}|2025-08-14 09:59:42  # noqa: E501
# 13|weather|{"call_id": "call_DWgN1qFAru8ScClVHj1jgqIz", "output": "Weather: Clear Sky, Temperature: 42.91\u00b0C (feels like 45.23\u00b0C), Humidity: 23%", "type": "function_call_output"}|2025-08-14 09:59:42  # noqa: E501
# 14|weather|{"id": "__fake_id__", "content": [{"annotations": [], "text": "Here is today's weather in major Israeli cities:\n\n- Tel Aviv: Clear sky, 36.9\u00b0C (feels like 40.23\u00b0C), 38% humidity\n- Jerusalem: Clear sky, 38.34\u00b0C (feels like 42.39\u00b0C), 36% humidity\n- Haifa: Clear sky, 33.39\u00b0C (feels like 34.41\u00b0C), 40% humidity\n- Eilat: Clear sky, 42.91\u00b0C (feels like 45.23\u00b0C), 23% humidity\n\nIt\u2019s a very hot and sunny day across the country\u2014plan accordingly!", "type": "output_text"}], "role": "assistant", "status": "completed", "type": "message"}|2025-08-14 09:59:42  # noqa: E501
