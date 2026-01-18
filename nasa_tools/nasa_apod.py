from dataclasses import dataclass
import http
from typing import List, Optional, Union
import requests
import os
from dotenv import load_dotenv
from langchain_core.tools import tool

@dataclass
class NASAAPOD:
    """
    Data model for the NASA Astronomy Picture of the Day (APOD).

    Attributes:
        apod_title: The title of the featured image or video.
        explanation: A detailed description of the astronomical feature.
        date: The date of publication (YYYY-MM-DD).
        multimedia_link: The direct URL to the media content.
        hd_multimedia_link: The URL for high-definition images (Image only).
        video_thumbnail_url: The URL for video previews (Video only).
        copyright_person_name: The name of the credit holder, if available.
    """
    apod_title: str
    explanation: str
    date: str
    multimedia_link: str
    hd_multimedia_link: Optional[str]
    video_thumbnail_url: Optional[str]
    copyright_person_name: Optional[str]

@dataclass
class NASAAPODResponse:
    """A container representing a collection of NASA APOD entries."""
    nasa_apods: List[NASAAPOD]

@dataclass
class ErrorDetails:
    """Represents a failed API request with relevant HTTP status and message."""
    status_code: int
    message: str

load_dotenv()
NASA_API_KEY = os.getenv("NASA_API_KEY") or "DEMO_KEY"


@tool
def get_nasa_apod(
    api_key: str = NASA_API_KEY, 
    apod_date: Optional[str] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    count: Optional[int] = None, 
    thumbs: bool = False
) -> Union[NASAAPODResponse, ErrorDetails]:
    """
    Fetches Astronomy Picture of the Day data from the NASA API.

    Args:
        api_key: NASA API key. Defaults to environment variable or "DEMO_KEY".
        apod_date: Date of the APOD to retrieve (YYYY-MM-DD).
        start_date: The start of a date range (YYYY-MM-DD).
        end_date: The end of a date range (YYYY-MM-DD).
        count: Number of random APODs to return.
        thumbs: If True, returns video thumbnail URLs.

    Returns:
        A NASAAPODResponse on success, or ErrorDetails if an error occurs.
    """
    params = {"api_key": api_key, "thumbs": thumbs}
    if count:
        params["count"] = count
    elif apod_date:
        params["date"] = apod_date
    elif start_date:
        params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
    
    try:
        # Added a timeout to prevent the script from hanging indefinitely
        api_response = requests.get(url="https://api.nasa.gov/planetary/apod", params=params, timeout=10)
        json_response = api_response.json()
    except Exception as e:
        return ErrorDetails(
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, 
            message=f"Failed to connect or parse JSON: {str(e)}"
        )

    if api_response.status_code != http.HTTPStatus.OK:
        # Extract the specific error message provided by NASA
        error_msg = json_response.get("msg") or json_response.get("error", {}).get("message", "Unknown error")
        return ErrorDetails(status_code=api_response.status_code, message=error_msg)
    
    # Ensure json_response is always a list for uniform processing
    raw_data_list = json_response if isinstance(json_response, list) else [json_response]

    nasa_apods: List[NASAAPOD] = []
    for item in raw_data_list:
        m_type = item.get("media_type")
        nasa_apods.append(
            NASAAPOD(
                apod_title=item.get("title", "Untitled"),
                explanation=item.get("explanation", ""),
                date=item.get("date", ""),
                multimedia_link=item.get("url", ""),
                copyright_person_name=item.get("copyright"), # None if missing
                hd_multimedia_link=item.get("hdurl") if m_type == "image" else None,
                video_thumbnail_url=item.get("thumbnail_url") if m_type == "video" else None
            )
        )
    
    return NASAAPODResponse(nasa_apods=nasa_apods)

# Usage
# result = get_nasa_apod.invoke(input={"apod_date":"2026-01-18"})

result = get_nasa_apod.invoke(input={})

print(result)
