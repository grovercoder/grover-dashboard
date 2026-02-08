from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import List, Optional
from pathlib import Path

class EmailAccount(BaseModel):
    name: str
    user: str
    password: str
    host: str 
    port: int = 993
    use_ssl: bool = True
    mailboxes: List[str] = ["INBOX"]
    
    def __str__(self):
        return f"{self.name} ({self.user})"

class WeatherConfig(BaseModel):
    city: str
    lat: float
    long: float
    units: str = "metric"

class WeatherResponse(BaseModel):
    code: int
    city: str
    temperature: float
    humidity: float
    wind_speed: float
    wind_units: str = "KPH"
    temp_units: str = "C"
    description: Optional[str] = None
    icon_class: Optional[str] = None

    @model_validator(mode="after")
    def compute_derived_fields(self) -> "WeatherResponse":
        weather_map = {
            0: ("Clear sky", "fa-sun"),
            1: ("Mainly clear", "fa-cloud-sun"),
            2: ("Partly cloudy", "fa-cloud-sun"),
            3: ("Overcast", "fa-cloud"),
            45: ("Fog", "fa-smog"),
            48: ("Depositing rime fog", "fa-smog"),
            51: ("Light drizzle", "fa-cloud-rain"),
            53: ("Moderate drizzle", "fa-cloud-rain"),
            55: ("Dense drizzle", "fa-cloud-showers-heavy"),
            56: ("Light freezing drizzle", "fa-icicles"),
            57: ("Dense freezing drizzle", "fa-icicles"),
            61: ("Slight rain", "fa-cloud-rain"),
            63: ("Moderate rain", "fa-cloud-showers-heavy"),
            65: ("Heavy rain", "fa-cloud-showers-heavy"),
            66: ("Light freezing rain", "fa-cloud-meatball"),
            67: ("Heavy freezing rain", "fa-cloud-meatball"),
            71: ("Slight snow fall", "fa-snowflake"),
            73: ("Moderate snow fall", "fa-snowflake"),
            75: ("Heavy snow fall", "fa-snowflake"), # fa-snowflakes is Pro only, snowflake is free
            77: ("Snow grains", "fa-box-tissue"),
            80: ("Slight rain showers", "fa-cloud-sun-rain"),
            81: ("Moderate rain showers", "fa-cloud-showers-heavy"),
            82: ("Violent rain showers", "fa-cloud-showers-water"),
            85: ("Slight snow showers", "fa-cloud-snow"),
            86: ("Heavy snow showers", "fa-cloud-snow"),
            95: ("Thunderstorm", "fa-bolt-lightning"),
            96: ("Thunderstorm with slight hail", "fa-cloud-bolt"),
            99: ("Thunderstorm with heavy hail", "fa-cloud-bolt")
        }
        
        desc, icon = weather_map.get(self.code, ("Unknown", "fa-question"))
        self.description = desc
        self.icon_class = icon
        return self

class DashboardConfig(BaseModel):
    weather: WeatherConfig
    email: List[EmailAccount]
    projects: List[Path]
