import requests


def get_weather(location: str) -> str:
    """Look up current weather for a location using the free Open-Meteo API.

    Returns a short plain-English description, e.g. "68°F, clear sky".
    """
    # Step 1: turn a place name into latitude/longitude (geocoding)
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},
        timeout=5,
    )
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        return f"I couldn't find a location called '{location}'."

    place = geo_data["results"][0]
    lat, lon = place["latitude"], place["longitude"]

    # Step 2: get current weather for those coordinates
    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "temperature_unit": "fahrenheit",
        },
        timeout=5,
    )
    weather_data = weather_response.json()
    current = weather_data["current"]

    temp = round(current["temperature_2m"])
    condition = _describe_weather_code(current["weather_code"])

    return f"{temp}°F, {condition}"


def _describe_weather_code(code: int) -> str:
    """Convert Open-Meteo's numeric weather code into plain English."""
    if code == 0:
        return "clear sky"
    elif code in (1, 2, 3):
        return "partly cloudy"
    elif code in (45, 48):
        return "foggy"
    elif code in range(51, 68):
        return "rainy"
    elif code in range(71, 78):
        return "snowy"
    elif code in range(80, 100):
        return "stormy"
    return "unknown conditions"
