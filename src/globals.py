import os

import supervisely as sly
from dotenv import load_dotenv

import flickr_api

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()
WORKSPACE_ID = sly.io.env.workspace_id()
PROJECT_ID = sly.io.env.project_id()
DATASET_ID = sly.io.env.dataset_id()

load_dotenv("flickr.env")
FLICKR_API_KEY = os.environ["FLICKR_API_KEY"]
FLICKR_API_SECRET = os.environ["FLICKR_API_SECRET"]

LICENSE_TYPE = 4
IMAGES_PER_PAGE = 500
REQUIRED_METADATA_KEYS = ["owner"]
OPTIONAL_METADATA_KEYS = ["title", "description"]

flickr_api.set_keys(FLICKR_API_KEY, FLICKR_API_SECRET)
