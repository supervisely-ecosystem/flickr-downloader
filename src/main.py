import os

from math import ceil

import flickr_api

from dotenv import load_dotenv

import supervisely as sly

IMAGES_PER_PAGE = 500
TEMP_DIR = "temp"

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()
workspace_id = int(os.environ["context.workspaceId"])


flickr_api_key = os.environ["FLICKR_API_KEY"]
flickr_api_secret = os.environ["FLICKR_API_SECRET"]

flickr_api.set_keys(flickr_api_key, flickr_api_secret)


def images_from_flicker(search_query, images_number, license_type=4):
    page_count = ceil(images_number / IMAGES_PER_PAGE)
    last_page_images_count = images_number % IMAGES_PER_PAGE
    pages = {i: IMAGES_PER_PAGE for i in range(1, page_count)}
    pages[page_count] = last_page_images_count

    images = []
    for page_number, images_per_page in pages.items():
        print(page_number, images_per_page)
        images += flickr_api.Photo.search(
            tags=search_query,
            per_page=images_per_page,
            license=license_type,
            page=page_number,
        )

    return images


def upload_images_to_dataset(dataset_id, images, metadata=None):
    for image in images:
        image_url = image.sizes["Original"]["source"]
        image_filename = os.path.basename(image_url)
        if metadata:
            image_metadata = get_image_metadata(image, metadata)
        else:
            image_metadata = None
        api.image.upload_link(
            dataset_id, image_filename, image_url, meta=image_metadata
        )


def get_image_metadata(image, metadata):
    photo_data = image.getInfo()
    result = {}
    for key in metadata:
        if key in photo_data:
            if key == "owner":
                owner_data = photo_data[key]
                result["owner_id"] = owner_data.id
                result["owner_username"] = owner_data.username
            else:
                result[key] = photo_data[key]
    return result


def create_project(project_name):
    project = api.project.create(
        workspace_id, project_name, change_name_if_conflict=True
    )
    return project.id


def create_dataset(project_id, dataset_name):
    dataset = api.dataset.create(project_id, dataset_name, change_name_if_conflict=True)
    return dataset.id


def flickr_to_supervisely(
    search_query: str,
    images_number: int,
    metadata: list = None,
    license_type: int = 4,
    **kwargs,
):
    project_id = kwargs.get("project_id")
    if not project_id:
        project_id = create_project(kwargs.get("project_name"))

    dataset_id = kwargs.get("dataset_id")
    if not dataset_id:
        dataset_id = create_dataset(project_id, kwargs.get("dataset_name"))

    images = images_from_flicker(search_query, images_number, license_type)

    upload_images_to_dataset(dataset_id, images, metadata)

    print(f"Successfully uploaded {len(images)} images from Flickr to Supervisely!")


existing_project_id = os.environ["context.projectId"]
existing_dataset_id = os.environ["context.datasetId"]
print("Existing project id:", existing_project_id)
print("Existing dataset id:", existing_dataset_id)


flickr_to_supervisely(
    "bicycle",
    10,
    project_id=existing_project_id,
    dataset_name="Flickr",
    metadata=["owner", "title", "description", "license"],
)
