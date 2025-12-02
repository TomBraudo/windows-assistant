"""
Image search/download tools for use in Word / PowerPoint documents.

Uses SerpAPI's image search to find a relevant picture, downloads it locally,
and returns the saved image path so other tools can insert it into documents.
"""

import os
import pathlib
from typing import Optional

import requests
from dotenv import load_dotenv


load_dotenv()

SERPAPI_ENDPOINT = "https://serpapi.com/search"


def _get_serpapi_key() -> Optional[str]:
    return os.getenv("SERPAPI_API_KEY")


def _default_image_dir() -> str:
    """
    Default location for downloaded images, under the user's Pictures folder
    if available, otherwise under the Desktop.
    """
    home = os.path.expanduser("~")
    pictures = os.path.join(home, "Pictures", "windows_agent_images")
    if not os.path.exists(os.path.dirname(pictures)):
        # Fallback to Desktop if Pictures doesn't exist
        pictures = os.path.join(home, "Desktop", "windows_agent_images")
    os.makedirs(pictures, exist_ok=True)
    return pictures


def find_image(query: str, save_dir: Optional[str] = None) -> str:
    """
    Finds a relevant image for the given query using SerpAPI Images, downloads it,
    and returns the local file path.

    This is intended as a helper for adding pictures into Word or PowerPoint:
    the agent can call this first to get an image file path, then pass that path
    into separate document tools.

    Args:
        query: Description of the desired image (e.g. "sunset over mountains").
        save_dir: Optional directory to save the image into. If omitted, a
                  'windows_agent_images' folder is created under Pictures or Desktop.

    Returns:
        On success: "Saved image to: <full_path>"
        On failure: An error message string describing what went wrong.
    """
    api_key = _get_serpapi_key()
    if not api_key:
        return "Error: SERPAPI_API_KEY is not configured in the environment."

    if not query or not query.strip():
        return "Error: Image search query is empty."

    if save_dir is None:
        save_dir = _default_image_dir()
    else:
        save_dir = os.path.abspath(save_dir)
        os.makedirs(save_dir, exist_ok=True)

    params = {
        "engine": "google_images",
        "q": query,
        "api_key": api_key,
        "num": 1,
    }

    try:
        resp = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Image search failed while contacting SerpAPI: {e}"

    images = data.get("images_results") or data.get("image_results") or []
    if not images:
        return f"No images found for query: '{query}'."

    first = images[0]
    url = first.get("original") or first.get("thumbnail") or first.get("link")
    if not url:
        return f"Image result for '{query}' is missing a usable URL."

    try:
        img_resp = requests.get(url, timeout=30)
        img_resp.raise_for_status()
    except Exception as e:
        return f"Failed to download image from '{url}': {e}"

    # Determine a reasonable filename
    parsed_name = pathlib.Path(url.split("?")[0]).name or "image"
    if not any(parsed_name.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
        parsed_name += ".jpg"

    filename = f"{query.strip().replace(' ', '_')}_{parsed_name}"
    safe_filename = "".join(c for c in filename if c not in '\\/:*?"<>|')
    full_path = os.path.join(save_dir, safe_filename)

    try:
        with open(full_path, "wb") as f:
            f.write(img_resp.content)
    except Exception as e:
        return f"Failed to save image to disk: {e}"

    return f"Saved image to: {full_path}"


