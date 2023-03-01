import os

from math import ceil
from time import sleep

from supervisely.app.widgets import (
    Container,
    Button,
    DestinationProject,
    Card,
    Progress,
    Text,
)

import src.globals as g
import src.ui.input as input
import src.ui.settings as settings

download_button = Button(text="Start download")
cancel_button = Button(text="Cancel download", button_type="danger")

cancel_button.hide()

progress = Progress()
progress.hide()

result_message = Text()
error_message = Text(status="error")

result_message.hide()
error_message.hide()

destination = DestinationProject(g.WORKSPACE_ID, project_type="images")

text_container = Container(widgets=[result_message, error_message])
buttons_container = Container(widgets=[download_button, cancel_button])

output_container = Container(
    widgets=[destination, progress, text_container, buttons_container],
    direction="vertical",
)
card = Card(
    "Choose destination",
    "Select destination for downloading images. If not filled the names will be generated automatically.",
    content=output_container,
)


def images_from_flicker(
    search_query: str, images_number: int, license_type: int
) -> list[g.flickr_api.objects.Photo]:
    """_summary_

    Args:
        search_query (str): query for searcging images on Flickr
        images_number (int): number of images to search
        license_type (int): type of the license for images

    Returns:
        list[g.flickr_api.objects.Photo]: list of Photo objects
    """
    # Calculate the number of pages to search depending on the number of images.
    page_count = ceil(images_number / g.IMAGES_PER_PAGE)
    # Calculate the number of images on the last page.
    last_page_images_count = images_number % g.IMAGES_PER_PAGE
    # Create a dictionary with the number of images to search on each page.
    pages = {i: g.IMAGES_PER_PAGE for i in range(1, page_count)}
    pages[page_count] = last_page_images_count

    images = []
    for page_number, images_per_page in pages.items():
        # Add images from the current page to the result list.
        images += g.flickr_api.Photo.search(
            tags=search_query,
            per_page=images_per_page,
            license=license_type,
            page=page_number,
        )

    return images


def upload_images_to_dataset(
    dataset_id: int, images: list[g.flickr_api.objects.Photo], metadata: list[str]
) -> int:
    """Uploads images to the specified dataset from the list of Photo objects.

    Args:
        dataset_id (int): the id of the dataset to upload images to
        images (list[g.flickr_api.objects.Photo]): list of Photo objects
        metadata (list[str]): list of metadata fields to add to images

    Returns:
        int: number of uploaded images
    """
    # Change the text on the download button and show the progress bar.
    download_button.text = "Downloading..."
    progress.show()

    with progress(
        message="Downloading images from Flickr...", total=len(images)
    ) as pbar:
        for image in images:
            # Check if the cancel button was clicked.
            if continue_downloading:
                # Get the URL of the original image and its filename.
                image_url = image.sizes["Original"]["source"]
                image_filename = os.path.basename(image_url)

                # Get the metadata of the image with the specified fields.
                image_metadata = get_image_metadata(image, metadata)

                # Upload the image to the dataset.
                g.api.image.upload_link(
                    dataset_id, image_filename, image_url, meta=image_metadata
                )
                pbar.update(1)

    return pbar.n


def get_image_metadata(
    image: g.flickr_api.objects.Photo, metadata: list[str]
) -> dict[str, str]:
    """Reads the metadata of the image for specified fields and returns it in a dictionary.

    Args:
        image (g.flickr_api.objects.Photo): Photo object to get metadata from
        metadata (list[str]): list of metadata fields to get

    Returns:
        dict[str, str]: dictionary with metadata fields and their values
    """
    # Get the metadata of the image.
    photo_data = image.getInfo()

    image_metadata = {}
    for key in metadata:
        # Check if the field is in the metadata of the image.
        if key in photo_data:
            # As long as the field owner is a dictionary, we need to get the id and username from it.
            if key == "owner":
                # Unpack the dictionary with the owner data.
                owner_data = photo_data[key]
                image_metadata["owner_id"] = owner_data.id
                image_metadata["owner_username"] = owner_data.username
            else:
                image_metadata[key] = photo_data[key]

    return image_metadata


@download_button.click
def flickr_to_supervisely():
    """Reads the data from the input fields and starts downloading images from Flickr."""
    # Show the cancel button and change the text on the download button.
    cancel_button.show()
    download_button.text = "Searching..."

    # Define the global variable to check if the download should continue.
    global continue_downloading
    continue_downloading = True

    # Define the global variable of search query to use it when creating project or dataset.
    global search_query
    search_query = input.search_query_input.get_value()

    images_number = input.images_number_input.get_value()

    # Reading global constants for the license type and metadata.
    license_type = g.LICENSE_TYPE
    metadata = g.REQUIRED_METADATA_KEYS

    # Add the metadata fields selected by the user to the list of metadata.
    metadata.extend(
        [
            key
            for key in settings.checkboxes.keys()
            if settings.checkboxes[key].is_checked()
        ]
    )

    # Getting the search results from Flickr.
    images = images_from_flicker(search_query, images_number, license_type)

    # Check if there are any images found for the query.
    if not images:
        # If there are no images, show the error message and hide the cancel button.
        error_message.text = "No images found for this query."

        download_button.text = "Finishing..."

        cancel_button.hide()
        error_message.show()
        sleep(3)
        error_message.hide()

    else:
        # If there are images, get the project and dataset ids.
        project_id, dataset_id = get_project_and_dataset_ids()

        # Upload the images to the dataset and get the number of uploaded images.
        uploaded_images_number = upload_images_to_dataset(dataset_id, images, metadata)

        cancel_button.hide()
        download_button.text = "Finishing..."

        show_result_message(uploaded_images_number)

    # Return the text on the download button to its original value.
    download_button.text = "Start download"


def show_result_message(uploaded_images_number: int):
    """Show the result message according to the global variable of continue_downloading
    and the number of uploaded images.

    Args:
        uploaded_images_number (int): the number of uploaded images
    """
    if continue_downloading:
        # If the download was not cancelled, prepare the success message.
        result_message.text = (
            f"Successfully downloaded {uploaded_images_number} images."
        )
        result_message.status = "success"
    else:
        # If the download was cancelled, prepare the warning message.
        result_message.text = (
            f"Download was cancelled after downloading {uploaded_images_number} images."
        )
        result_message.status = "warning"

    # Show the result message and hide it after 3 seconds.
    result_message.show()
    sleep(3)
    result_message.hide()


def get_project_and_dataset_ids() -> tuple[int]:
    """If the project or dataset does not exist, create it and return its id.
    Otherwise, return the id of the existing project and dataset.

    Returns:
        tuple[int]: tuple with project and dataset ids
    """
    # Read the project and dataset ids from the destination input.
    project_id = destination.get_selected_project_id()
    dataset_id = destination.get_selected_dataset_id()

    # If the project or dataset does not exist, create it.
    if not project_id:
        project_id = create_project(destination.get_project_name())
    if not dataset_id:
        dataset_id = create_dataset(project_id, destination.get_dataset_name())

    return project_id, dataset_id


def create_project(project_name: str | None) -> int:
    """Create the project with the specified name and return its id.
    If the name is not specified, use the search query as the name.

    Args:
        project_name (str | None): name of the project to create

    Returns:
        int: id of the created project
    """
    # If the name is not specified, use the search query as the name.
    if not project_name:
        project_name = f"Flickr images: {search_query}"

    project = g.api.project.create(
        g.WORKSPACE_ID, project_name, change_name_if_conflict=True
    )
    return project.id


def create_dataset(project_id: int, dataset_name: str | None) -> int:
    """Create the dataset with the specified name and return its id.
    If the name is not specified, use the search query as the name.

    Args:
        project_id (int): id of the project to create the dataset in
        dataset_name (str | None): name of the dataset to create

    Returns:
        int: id of the created dataset
    """
    # If the name is not specified, use the search query as the name.
    if not dataset_name:
        dataset_name = f"Flickr images: {search_query}"

    dataset = g.api.dataset.create(
        project_id, dataset_name, change_name_if_conflict=True
    )
    return dataset.id


@cancel_button.click
def cancel_downloading():
    """Changes the global variable of continue_downloading to False to stop downloading images,
    and hides the cancel button."""
    global continue_downloading
    continue_downloading = False
    cancel_button.hide()
