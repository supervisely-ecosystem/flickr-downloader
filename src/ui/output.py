import os

from math import ceil

from supervisely.app.widgets import Container, Button, DestinationProject, Card

import src.globals as g
import src.ui.input as input

download_button = Button(text="Start downloading images")
cancel_button = Button(text="Cancel downloading", button_type="danger")
cancel_button.hide()
destination = DestinationProject(g.WORKSPACE_ID, project_type="images")
destination_container = Container(
    widgets=[destination, download_button, cancel_button], direction="vertical"
)
card = Card(
    "Choose destination",
    "Select destination for downloading images",
    content=destination_container,
)


def images_from_flicker(search_query: str, images_number: int, license_type: int = 4):
    page_count = ceil(images_number / g.IMAGES_PER_PAGE)
    last_page_images_count = images_number % g.IMAGES_PER_PAGE
    pages = {i: g.IMAGES_PER_PAGE for i in range(1, page_count)}
    pages[page_count] = last_page_images_count

    images = []
    for page_number, images_per_page in pages.items():
        images += g.flickr_api.Photo.search(
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
        image_metadata = get_image_metadata(image, metadata)
        g.api.image.upload_link(
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
    project = g.api.project.create(
        g.WORKSPACE_ID, project_name, change_name_if_conflict=True
    )
    return project.id


def create_dataset(project_id, dataset_name):
    dataset = g.api.dataset.create(
        project_id, dataset_name, change_name_if_conflict=True
    )
    return dataset.id


@download_button.click
def flickr_to_supervisely():
    search_query = input.search_query_input.get_value()
    images_number = input.images_number_input.get_value()

    license_type = 4  # MOVE TO VARIABLES!
    metadata = ["owner"]  # READ FROM PAGE!

    project_id = destination.get_selected_project_id()
    dataset_id = destination.get_selected_dataset_id()

    if not project_id:
        project_id = create_project(destination.get_project_name())

    if not dataset_id:
        dataset_id = create_dataset(project_id, destination.get_dataset_name())

    images = images_from_flicker(search_query, images_number, license_type)

    upload_images_to_dataset(dataset_id, images, metadata)

    print(f"Successfully uploaded {len(images)} images from Flickr to Supervisely!")
