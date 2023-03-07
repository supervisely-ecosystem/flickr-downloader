import os

import supervisely as sly
from dotenv import load_dotenv

import flickr_api

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()
WORKSPACE_ID = sly.io.env.workspace_id()
PROJECT_ID = sly.io.env.project_id()
DATASET_ID = sly.io.env.dataset_id()

SLY_APP_DATA_DIR = os.environ["SLY_APP_DATA_DIR"]
IMAGES_TMP_DIR = "images"

# The size of the batch of images to download.
BATCH_SIZE = 10
MAX_WORKERS = 5

# Flickr API init with keys from .env file.
load_dotenv("flickr.env")
FLICKR_API_KEY = os.environ["FLICKR_API_KEY"]
FLICKR_API_SECRET = os.environ["FLICKR_API_SECRET"]

# Constant settings for images search.
LICENSE_TYPES = {
    "CC BY-SA": 1,
    "CC BY-NC": 2,
    "CC BY: Attribution": 4,
    "CC0": 9,
    "PDM": 10,
}
# Inverted dictionary for getting text representation of license type by its number.
LICENSE_TYPES_BY_NUMBER = {v: k for k, v in LICENSE_TYPES.items()}

IMAGES_PER_PAGE = 500
REQUIRED_METADATA_FIELDS = ["owner", "license"]
OPTIONAL_METADATA_FIELDS = ["id", "title", "description"]
DOWNLOAD_TYPES = ["links", "files"]

flickr_api.set_keys(FLICKR_API_KEY, FLICKR_API_SECRET)
