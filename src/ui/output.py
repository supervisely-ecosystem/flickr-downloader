import os
import requests

from datetime import datetime
from shutil import rmtree
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

import supervisely as sly
from supervisely.app.widgets import (
    Container,
    Button,
    DestinationProject,
    Card,
    Progress,
    Text,
    DatasetThumbnail,
)

import src.globals as g
import src.ui.keys as keys
import src.ui.input as input
import src.ui.settings as settings

download_button = Button(text="Start upload")
cancel_button = Button(text="Cancel upload", button_type="danger")

cancel_button.hide()

progress = Progress()
progress.hide()

result_message = Text()
result_message.hide()

destination = DestinationProject(g.WORKSPACE_ID, project_type="images")

dataset_thumbnail = DatasetThumbnail(show_project_name=True)
dataset_thumbnail.hide()

# Main card for all output widgets.
card = Card(
    "Choose destination",
    "Select the destination for downloading images. If not filled the names will be generated automatically. ",
    content=Container(
        widgets=[
            destination,
            progress,
            download_button,
            cancel_button,
            result_message,
            dataset_thumbnail,
        ],
        direction="vertical",
    ),
    lock_message="Please, enter API key and check the connection to the Flickr API.",
)
card.lock()


def images_from_flicker(
    search_query: str,
    images_number: int,
    license_type: List[int],
    metadata: List[str],
    start_number: int,
) -> Tuple[List[str], List[str], List[Dict[str, str]]]:
    """Searches for specified number of images on Flickr using the specified search query
    and returns the list of image names, links and metadata with specified fields.

    Args:
        search_query (str): search query for images
        images_number (int): number of images to search
        license_type (List[int]): license types for images to search
        metadata (List[str]): list of metadata fields to add for images
        start_number (int): number of images to skip from the beginning of the search

    Returns:
        tuple[List[str], List[str], List[Dict[str, str]]]: returns the list of image names,
        links and metadata for using in the upload_links() function
    """
    # Calculate the number of pages and images on the last page according to
    # the number of images to search and start number.
    total_images_number = images_number + start_number
    start_page_number = start_number // g.IMAGES_PER_PAGE + 1
    start_offset_number = start_number % g.IMAGES_PER_PAGE

    # Create a dictionary with the number of images per page.
    full_pages_number = total_images_number // g.IMAGES_PER_PAGE
    pages = {i: g.IMAGES_PER_PAGE for i in range(1, full_pages_number + 1)}
    last_page_images_number = total_images_number % g.IMAGES_PER_PAGE
    if last_page_images_number:
        pages[full_pages_number + 1] = last_page_images_number

    sly.logger.debug(
        f"Paging: {pages}, start page: {start_page_number}, start offset: {start_offset_number}."
    )
    # Check if adding images to an existing dataset.
    global dataset_id
    if dataset_id:
        # Read the list of existing file names to check for duplicates in search results.
        sly.logger.debug(f"Dataset ID is not None: {dataset_id}.")
        existing_names = [image.name for image in g.api.image.get_list(dataset_id)]
        sly.logger.debug(f"Read {len(existing_names)} existing names from the dataset.")
        sly.logger.debug(f"Examples: {existing_names[:5]}")

    # Debug variables to count the number of filtered images and duplicates. Delete in production.
    filtered_images = 0
    existed_duplicates = 0

    names = []
    links = []
    metas = []
    # Debug timer, delete in production.
    global full_flickr_search_time
    full_flickr_search_time = 0

    for page_number in range(start_page_number, len(pages) + 1):
        images_per_page = pages[page_number]
        sly.logger.debug(
            f"Page number: {page_number}. Images per page: {images_per_page}."
        )

        # Test time of API response, delete in production.
        init_call_time = perf_counter()
        images_on_page = keys.flickr_api.Photo.search(
            text=search_query,
            sort=g.SORT_TYPE,
            content_type=g.CONTENT_TYPE,
            media=g.MEDIA_TYPE,
            per_page=images_per_page,
            license=",".join([str(i) for i in license_type]),
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

        if page_number == start_page_number:
            # Slice the list of images on the first page according to the start offset.
            sly.logger.debug(
                f"Page number {page_number} is equal to start page number {start_page_number}. Slicing the result "
                f"list of images with {start_offset_number} offset."
            )
            images_on_page = images_on_page[start_offset_number:]

        # Iterate over the list of images on the current page.
        for image in images_on_page:
            image_as_dict = image.__dict__
            # Extract the link to the original image.
            link = image_as_dict.get("url_o")
            # Checking if the link is correct and the image is not a duplicate in search results.
            if not link or not link.endswith(".jpg") or link in links:
                filtered_images += 1
                sly.logger.debug(
                    f"Image with id {image_as_dict.get('id')} is skipped due "
                    f"to no link, wrong extension or as duplicate."
                )
                continue
            # Extract the name of the image from the link
            name = os.path.basename(link)
            # Check if the image already exists in the dataset if adding images to an existing dataset.
            if dataset_id and name in existing_names:
                existed_duplicates += 1
                sly.logger.debug(
                    f"Image with name {name} is skipped because it already exists in the dataset."
                )
                continue

            names.append(name)
            links.append(link)
            metas.append(get_image_metadata(image_as_dict, metadata))

    # Debug code to check if the lists contain duplicates and have the same length.
    # Delete in production.
    sly.logger.debug(
        f"Flickr API returned {len(names) +  filtered_images + existed_duplicates} images for "
        f"search query with {images_number} images number."
    )
    sly.logger.debug(
        f"Skipped {existed_duplicates} number of images already existed in the dataset."
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
        f"Total number of results after filtering: {len(names)}. {filtered_images} was filtered as bad results. "
        f"{existed_duplicates} was filtered as duplicates."
    )
    return names, links, metas


def download_images(
    names: List[str], links: List[str], metas: List[Dict[str, str]]
) -> Tuple[List[str], List[str], List[Dict[str, str]]]:
    """Downloads the images with specified links to the local temporary directory.
    Filters names and metas to match the downloaded images.

    Args:
        names (List[str]): names of the files to download
        links (List[str]): global links to the files to download
        metas (List[Dict[str, str]]): metadata for the files to download

    Returns:
        Tuple[List[str], List[str], List[Dict[str, str]]]: returns the list of local image names,
        paths to the files and metadata for using in the upload_paths() function.
    """
    # Debug variable to calculate time of image downloads. Delete in production.
    start_time = perf_counter()

    cancel_button.text = "Cancel upload"

    # Creating the temporary directory for images.
    outpur_dir = os.path.join(g.SLY_APP_DATA_DIR, g.IMAGES_TMP_DIR)
    os.makedirs(outpur_dir, exist_ok=True)

    local_names = []
    local_links = []
    local_metas = []

    def download_image(link: str, image_number: int):
        """Downloads the image with specified link to the local temporary directory.

        Args:
            global_link (str): global link to the file to download
            image_number (int): number of the image in the global lists to filter
            metas and names lists according to the downloaded images.
            progress (Progress): progress object to update when downloading the image.
        """
        name = names[image_number]
        meta = metas[image_number]

        response = requests.get(link)
        # Creating path for image to download.
        local_link = os.path.join(outpur_dir, name)

        try:
            # Writing the image to the local temporary directory.
            with open(local_link, "wb") as fo:
                fo.write(response.content)
            # Adding data to the local lists if the image was downloaded successfully.
            local_names.append(name)
            local_links.append(local_link)
            local_metas.append(meta)

            sly.logger.debug(
                f"Image #{image_number} downloaded successfully as {local_link}."
            )
        except Exception as error:
            sly.logger.error(
                f"There was an error while downloading the image #{image_number}: {error}."
            )

    with ThreadPoolExecutor(max_workers=g.MAX_WORKERS) as executor:
        # Number of the image in the global lists to access the metadata and names.
        for image_number, link in enumerate(links):
            executor.submit(download_image, link, image_number)

    # Debug code to calculate time of image downloads. Delete in production.
    end_time = perf_counter()
    sly.logger.debug(
        f"Downloaded {len(local_names)} images in {end_time - start_time} seconds"
    )
    # Debug check if the lists have the same length. Delete in production.
    sly.logger.debug(
        f"All objects have similar length: {len(local_names) == len(local_links) == len(local_metas)}"
    )

    return local_names, local_links, local_metas


def upload_images_to_dataset(
    dataset_id: int,
    batch_names: List[str],
    batch_links: List[str],
    batch_metas: List[Dict[str, str]],
    upload_method: str,
) -> int:
    """Adds images to the specified dataset using the list of names, links and metadata in batches.

    Args:
        dataset_id (int): the ID of the dataset to add images to
        batch_names (List[str]): list with images filenames
        batch_links (List[str]): list with images links
        batch_metas (List[Dict[str, str]]): list with images metadata
        upload_method (str): the method to upload images to the dataset
    Returns:
        int: the number of uploaded images
    """

    sly.logger.debug(
        f"Starting to upload {len(batch_names)} images to dataset {dataset_id} with {upload_method} upload method."
    )
    # Check if the user hasn't pressed the cancel button.
    if continue_downloading:
        if upload_method == "links":
            uploaded_images = g.api.image.upload_links(
                dataset_id, batch_names, batch_links, metas=batch_metas
            )
        elif upload_method == "files":
            uploaded_images = g.api.image.upload_paths(
                dataset_id, batch_names, batch_links, metas=batch_metas
            )

        sly.logger.debug(
            f"Finished uploading batch with {len(uploaded_images)} images to dataset {dataset_id}."
        )

        return len(uploaded_images)


def get_image_metadata(
    image_as_dict: Dict[str, str], metadata: List[str]
) -> Dict[str, str]:
    """Returns the dictionary with the specified metadata fields for the image.

    Args:
        image_as_dict (Dict[str, str]): dictionary which containts image attributes
        metadata (List[str]): list of metadata fields to add for images

    Returns:
        Dict[str, str]: dictionary with the specified metadata fields for the
        image to use with upload_links() function
    """
    image_metadata = {"Flickr image URL": image_as_dict.get("url_o")}

    for key in metadata:
        if key == "owner":
            # Unpacking the owner object to get the owner id.
            owner = image_as_dict.get(key).__dict__
            image_metadata["Flickr owner id"] = owner.get("id")
        elif key == "license":
            # Retrieving the license text by its number.
            license_number = int(image_as_dict.get(key))
            image_metadata[key] = g.LICENSE_TYPES_BY_NUMBER[license_number]
        elif key == "id":
            image_metadata["Flickr image ID"] = image_as_dict.get(key)
        else:
            image_metadata[key.title()] = image_as_dict.get(key)

    return image_metadata


@download_button.click
def flickr_to_supervisely():
    """Reads the data from the input fields and starts downloading images from Flickr."""
    # Hiding all info messages after the download button was pressed.
    settings.license_message.hide()
    input.query_message.hide()
    result_message.hide()
    dataset_thumbnail.hide()

    license_type = settings.select_license.get_value()
    if not license_type:
        settings.license_message.show()
        return

    # Define the global variable of search query to use it when creating project or dataset.
    global search_query
    search_query = input.search_query_input.get_value()
    if not search_query:
        input.query_message.show()
        return

    # Test time of the whole function, delete in production.
    start_time = perf_counter()
    # Show the cancel button and change the text on the download button.
    cancel_button.text = "Cancel search"
    download_button.text = "Searching..."
    cancel_button.show()

    # Read the project and dataset ids from the destination input.
    # Define the global variables to use them in show_result_message().
    global project_id
    project_id = destination.get_selected_project_id()
    global dataset_id
    dataset_id = destination.get_selected_dataset_id()

    # Define the global variable to check if the download should continue.
    global continue_downloading
    continue_downloading = True

    images_number = input.images_number_input.get_value()

    start_number = settings.start_number_input.get_value()

    # Reading global constant for required metadata fields.
    metadata = [
        key
        for key in settings.disabled_chekboxes.keys()
        if settings.disabled_chekboxes[key].is_checked()
    ]
    # Add the metadata fields selected by the user to the list of metadata.
    metadata.extend(
        [
            key
            for key in settings.checkboxes.keys()
            if settings.checkboxes[key].is_checked()
        ]
    )
    sly.logger.debug(
        f"Started with the following parameters: Search query: {search_query}; Start number: {start_number};"
        f"Images number: {images_number}; License types: {license_type}; Metadata: {metadata};"
    )

    # Get the lists of names, links and metadata for the search results.
    names, links, metas = images_from_flicker(
        search_query, images_number, license_type, metadata, start_number
    )

    upload_method = settings.upload_method_radio.get_value()

    # Check if there are any images found for the query.
    if not (names and links and metas):  # Move to function?
        # If there are no images, show the error message.
        show_result_message(error=True)
        return

    # Test time of the upload function, delete in production.
    before_upload_time = perf_counter()
    search_and_prepare_time = before_upload_time - start_time
    sly.logger.debug(
        f"Search and prepare time: {search_and_prepare_time} seconds. Time "
        f"excluding API requests: {search_and_prepare_time - full_flickr_search_time} seconds."
    )

    # Create the project and dataset if they don't exist.
    if not project_id:
        project_id = create_project(destination.get_project_name())
    if not dataset_id:
        dataset_id = create_dataset(project_id, destination.get_dataset_name())

    progress.show()
    uploaded_images_number = 0

    with progress(
        message="Uploading images to the dataset...", total=len(names)
    ) as pbar:
        # Batch the lists of names, links and metadata.
        for batch_names, batch_links, batch_metas in zip(
            sly.batched(names, batch_size=g.BATCH_SIZE),
            sly.batched(links, batch_size=g.BATCH_SIZE),
            sly.batched(metas, batch_size=g.BATCH_SIZE),
        ):
            # Nullify the variable for each batch.
            uploaded_batch_images_number = 0

            # Check if the cancel button was pressed.
            if continue_downloading:
                download_button.text = "Uploading..."
                cancel_button.text = "Cancel upload"

                if upload_method == "files":
                    # If the upload method is files, download the images instead of using the links.
                    batch_names, batch_links, batch_metas = download_images(
                        batch_names, batch_links, batch_metas
                    )

                # Upload the batch of images to the dataset.
                uploaded_batch_images_number = upload_images_to_dataset(
                    dataset_id, batch_names, batch_links, batch_metas, upload_method
                )
            if uploaded_batch_images_number:
                # Update the progress bar and the number of uploaded images.
                uploaded_images_number += uploaded_batch_images_number
                pbar.update(uploaded_batch_images_number)

    # Debug variable to test the time of the whole function, delete in production.
    end_time = perf_counter()
    sly.logger.debug(f"Time: {end_time - start_time} seconds")

    # Preparing defaultdict for custom_data from project.
    custom_data = defaultdict(dict)

    # Update the custom_data with the data from the project.
    custom_data.update(g.api.project.get_info_by_id(project_id).custom_data)

    # Adding app search results to the custom_data of the project.
    search_query_dict = custom_data[g.CUSTOM_DATA_KEY].get(search_query, {})
    search_query_dict.update(
        {
            datetime.now().strftime("%Y/%m/%d %H:%M:%S"): {
                "Dataset name": g.api.dataset.get_info_by_id(dataset_id).name,
                "Search images offset": start_number,
                "Number of images": uploaded_images_number,
                "License types": ", ".join(
                    g.LICENSE_TYPES_BY_NUMBER[number] for number in license_type
                ),
            }
        }
    )

    # Updating custom_data with the new data.
    custom_data[g.CUSTOM_DATA_KEY][search_query] = search_query_dict
    g.api.project.update_custom_data(project_id, dict(custom_data))

    # Delete the temporary directory with images.
    rmtree(g.SLY_APP_DATA_DIR, ignore_errors=True)

    show_result_message(uploaded_images_number)


def show_result_message(uploaded_images_number: Optional[int] = 0, error: bool = False):
    """Show the result message according to the global variable of continue_downloading
    and the number of uploaded images.

    Args:
        uploaded_images_number (Optional[int]): the number of uploaded images
        error (bool): if there was an error during the download
    """
    cancel_button.hide()
    if project_id and dataset_id:
        project = g.api.project.get_info_by_id(project_id)
        dataset = g.api.dataset.get_info_by_id(id=dataset_id)
        dataset_thumbnail.set(project, dataset)

    if error:
        result_message.text = "No images found for this query."
        result_message.status = "error"
    elif continue_downloading:
        # If the upload was not cancelled, prepare the success message.
        result_message.text = f"Successfully uploaded {uploaded_images_number} images."
        result_message.status = "success"
        dataset_thumbnail.show()
    elif uploaded_images_number:
        # If the upload was cancelled, prepare the warning message.
        result_message.text = (
            f"Download was cancelled after uploading {uploaded_images_number} images."
        )
        result_message.status = "warning"
        dataset_thumbnail.show()
    else:
        # If the upload was cancelled and no images were uploaded, prepare the error message.
        result_message.text = "Download was cancelled. No images were uploaded."
        result_message.status = "error"

    # Show the result message and hide it after 3 seconds.
    result_message.show()
    download_button.text = "Start upload"


def create_project(project_name: Optional[str]) -> int:
    """Create the project with the specified name and return its id.
    If the name is not specified, use the search query as the name.

    Args:
        project_name (Optional[str]): name of the project to create

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


def create_dataset(project_id: int, dataset_name: Optional[str]) -> int:
    """Create the dataset with the specified name and return its id.
    If the name is not specified, use the search query as the name.

    Args:
        project_id (int): id of the project to create the dataset in
        dataset_name (Optional[str]): name of the dataset to create

    Returns:
        int: id of the created dataset
    """
    # If the name is not specified, use the search query as the name.
    if not dataset_name:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sly.logger.debug("Dataset name is not specified, using search query.")
        dataset_name = f"{now} Flickr search: {search_query}"

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
