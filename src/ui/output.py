import os

from math import ceil
from time import sleep, perf_counter

import supervisely as sly
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
    "Select the destination for downloading images. If not filled the names will be generated automatically. ",
    content=output_container,
)


def images_from_flicker(
    search_query: str, images_number: int, license_type: int, metadata: list[str]
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    """Searches for specified number of images on Flickr using the specified search query
    and returns the list of image names, links and metadata with specified fields.

    Args:
        search_query (str): search query for images
        images_number (int): number of images to search
        license_type (int): license type for images (4 for Creative Commons Attribution-NonCommercial)
        metadata (list[str]): list of metadata fields to add for images

    Returns:
        tuple[list[str], list[str], list[dict[str, str]]]: returns the list of image names,
        links and metadata for using in the upload_links() function
    """
    # Calculate the number of pages to search depending on the number of images.
    page_count = ceil(images_number / g.IMAGES_PER_PAGE)
    # Calculate the number of images on the last page.
    last_page_images_count = images_number % g.IMAGES_PER_PAGE
    # Create a dictionary with the number of images to search on each page.
    pages = {i: g.IMAGES_PER_PAGE for i in range(1, page_count + 1)}
    if last_page_images_count:
        pages[page_count] = last_page_images_count

    # Debug variable to count the number of filtered images. Delete in production.
    filtered_images = 0

    names = []
    links = []
    metas = []
    # Debug timer, delete in production.
    global full_flickr_search_time
    full_flickr_search_time = 0

    for page_number, images_per_page in pages.items():
        # Get the list of images on the current page.
        # Test time of API response, delete in production.
        init_call_time = perf_counter()
        images_on_page = g.flickr_api.Photo.search(
            text=search_query,
            sort="relevance",
            content_type=1,
            media="photos",
            per_page=images_per_page,
            license=license_type,
            page=page_number,
            extras=",".join(metadata),
        )
        # Test time of API response, delete in production.
        end_call_time = perf_counter()
        flickr_search_time = end_call_time - init_call_time
        full_flickr_search_time += flickr_search_time

        sly.logger.debug(
            f"Time of Flickr API response: {flickr_search_time} for {images_per_page} images."
        )
        # Iterate over the list of images on the current page.
        for image in images_on_page:
            image_as_dict = image.__dict__
            link = image_as_dict.get("url_o")
            if not link or not link.endswith(".jpg") or link in links:
                filtered_images += 1
                sly.logger.warning(
                    f"Image with id {image_as_dict.get('id')} is skipped due "
                    f"to no link, wrong extension or as duplicate."
                )
                continue
            name = os.path.basename(link)
            names.append(name)
            links.append(link)
            metas.append(get_image_metadata(image_as_dict, metadata))

    # Debug code to check if the lists contain duplicates and have the same length.
    # Delete in production.
    sly.logger.debug(
        f"Flickr API returned {len(names) +  filtered_images} images for "
        f"search query with {images_number} images number."
    )
    sly.logger.debug(f"Full Flickr API search time: {full_flickr_search_time}")
    sly.logger.debug(
        f"Names list doesn't contain duplicates: {len(names) == len(set(names))}"
    )
    sly.logger.debug(
        f"Links list doesn't contain duplicates: {len(links) == len(set(links))}"
    )
    sly.logger.debug(
        f"All objects have similar length: {len(names) == len(links) == len(metas)}"
    )
    sly.logger.debug(
        f"Total number of filtered results: {len(names)}. {filtered_images} was filtered as bad results."
    )
    return names, links, metas


def upload_images_to_dataset(
    dataset_id: int, names: list[str], links: list[str], metas: list[dict[str, str]]
) -> int:
    """Adds images to the specified dataset using the list of names, links and metadata in batches.

    Args:
        dataset_id (int): the ID of the dataset to add images to
        names (list[str]): list with images filenames
        links (list[str]): list with images links
        metas (list[dict[str, str]]): list with images metadata

    Returns:
        int: the number of uploaded images
    """

    sly.logger.debug(
        f"Starting to upload images to dataset {dataset_id}. Number of images: {len(names)}"
    )

    progress.show()
    uploaded_images_number = 0

    with progress(
        message="Downloading images from Flickr...", total=len(names)
    ) as pbar:
        # Batch the lists of names, links and metadata.
        for batch_names, batch_links, batch_metas in zip(
            sly.batched(names, batch_size=g.BATCH_SIZE),
            sly.batched(links, batch_size=g.BATCH_SIZE),
            sly.batched(metas, batch_size=g.BATCH_SIZE),
        ):
            # Check if the user hasn't pressed the cancel button.
            if continue_downloading:
                # Change the text on the download button and show the progress bar.
                download_button.text = "Downloading..."
                uploaded_images = g.api.image.upload_links(
                    dataset_id, batch_names, batch_links, metas=batch_metas
                )
                pbar.update(g.BATCH_SIZE)
                uploaded_images_number += len(uploaded_images)

    return uploaded_images_number


def get_image_metadata(
    image_as_dict: dict[str, str], metadata: list[str]
) -> dict[str, str]:
    """Returns the dictionary with the specified metadata fields for the image.

    Args:
        image_as_dict (dict[str, str]): dictionary which containts image attributes
        metadata (list[str]): list of metadata fields to add for images

    Returns:
        dict[str, str]: dictionary with the specified metadata fields for the
        image to use with upload_links() function
    """

    image_metadata = {
        "License type": license_text,
    }

    for key in metadata:
        if key == "owner":
            owner = image_as_dict.get(key).__dict__
            image_metadata["Owner id"] = owner.get("id")
        else:
            image_metadata[key.title()] = image_as_dict.get(key)
    return image_metadata


@download_button.click
def flickr_to_supervisely():
    """Reads the data from the input fields and starts downloading images from Flickr."""
    # Test time of the whole function, delete in production.
    start_time = perf_counter()
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
    license_type = settings.select_license.get_value()
    global license_text
    license_text = g.LICENSE_TYPES_BY_NUMBER[license_type]

    # Reading global constant for required metadata fields.
    metadata = g.REQUIRED_METADATA_KEYS

    # Add the metadata fields selected by the user to the list of metadata.
    metadata.extend(
        [
            key
            for key in settings.checkboxes.keys()
            if settings.checkboxes[key].is_checked()
        ]
    )
    sly.logger.debug(
        f"Started with the following parameters: Search query: {search_query}; "
        f"Images number: {images_number}; License type: {license_type}; Metadata: {metadata};"
    )

    # Get the lists of names, links and metadata for the search results.
    names, links, metas = images_from_flicker(
        search_query, images_number, license_type, metadata
    )

    # Check if there are any images found for the query.
    if not (names and links and metas):
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

        # Test time of the upload function, delete in production.
        before_upload_time = perf_counter()
        search_and_prepare_time = before_upload_time - start_time
        sly.logger.debug(
            f"Search and prepare time: {search_and_prepare_time} seconds. Time "
            f"excluding API requests: {search_and_prepare_time - full_flickr_search_time} seconds."
        )
        # Upload the images to the dataset and get the number of uploaded images.
        uploaded_images_number = upload_images_to_dataset(
            dataset_id, names, links, metas
        )

        cancel_button.hide()
        download_button.text = "Finishing..."

        end_time = perf_counter()
        print(f"Time: {end_time - start_time} seconds")

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
        sly.logger.debug("Project name is not specified, using search query.")
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
        sly.logger.debug("Dataset name is not specified, using search query.")
        dataset_name = f"Flickr images: {search_query}"

    dataset = g.api.dataset.create(
        project_id, dataset_name, change_name_if_conflict=True
    )
    return dataset.id


@cancel_button.click
def cancel_downloading():
    """Changes the global variable of continue_downloading to False to stop downloading images,
    hides the cancel button and changes the text on download button."""
    global continue_downloading
    continue_downloading = False
    download_button.text = "Stopping..."
    cancel_button.hide()
