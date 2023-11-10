import os

from typing import Optional

import supervisely as sly

from dotenv import load_dotenv

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()

TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()

SLY_APP_DATA_DIR = sly.app.get_data_dir()
IMAGES_TMP_DIR = "images"
CUSTOM_DATA_KEY = "Flickr downloader"

FLICKR_API_URL = "https://www.flickr.com/services/rest/"
FLICKR_SOURCE_URL = "https://www.flickr.com/photos/{owner}/{id}"

PARAMS = {
    "method": "flickr.photos.search",
    "sort": "relevance",
    "content_type": 1,
    "format": "json",
    "nojsoncallback": 1,
}

# Available license types for images: keys are text representations, values are codes in the Flickr API.
LICENSE_TYPES = {
    "CC BY-SA": 1,
    "CC BY-NC": 2,
    "CC BY: Attribution": 4,
    "NKCR": 7,
    "CC0": 9,
    "PDM": 10,
}
# Inverted dictionary for getting text representation of license type by its number.
LICENSE_TYPES_BY_NUMBER = {v: k for k, v in LICENSE_TYPES.items()}

# Settings for images search and metadata fields.
IMAGES_PER_PAGE = 500

SEARCH_TYPES = ["text", "tags"]
TAGS_TYPES = ["any", "all"]

REQUIRED_METADATA_FIELDS = {
    "Photographer name": "owner_name",
    "Source URL": "source_url",
    "License": "license",
}
REQUIRED_METADATA_FIELDS_BY_KEY = {v: k for k, v in REQUIRED_METADATA_FIELDS.items()}

OPTIONAL_METADATA_FIELDS = {
    "Image title": "title",
    "Image description": "description",
}
OPTIONAL_METADATA_FIELDS_BY_KEY = {v: k for k, v in OPTIONAL_METADATA_FIELDS.items()}

# Download types for images.
DOWNLOAD_TYPES = {
    "files": "Copy source file to the Supervisely dataset",
    "links": "Add link to source image in the Supervisely dataset",
}
ALLOWED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png"]


def key_from_file() -> Optional[str]:
    """Tries to load Flickr API key from the team files.

    Returns:
        Optional[str]: returns Flickr API key if it was loaded successfully, None otherwise.
    """
    try:
        # Get flickr.env from the team files.
        INPUT_FILE = sly.env.file(True)
        api.file.download(TEAM_ID, INPUT_FILE, "flickr.env")

        # Read Flickr API key from the file.
        load_dotenv("flickr.env")
        FLICKR_API_KEY = os.environ["FLICKR_API_KEY"]

        sly.logger.info("Flickr API key was loaded from the team files.")
        return FLICKR_API_KEY
    except Exception as error:
        sly.logger.debug(
            f"Flickr API key was not loaded from the team files with error: {error}.)"
        )
