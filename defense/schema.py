from pydantic import BaseModel

class WeatherRequest(BaseModel):
    location: str
    date: str = None # type: ignore