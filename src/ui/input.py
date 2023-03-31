import requests

import supervisely as sly

from supervisely.app.widgets import (
    Input,
    Container,
    Card,
    Text,
    Field,
    Button,
    Select,
)

import src.ui.keys as keys
import src.globals as g

query_message = Text(status="error", text="Please, enter the search query.")
query_message.hide()

# Generate search type selector.
search_type_select = Select(
    items=[Select.Item(value=type, label=type.capitalize()) for type in g.SEARCH_TYPES]
)

# Field for search type selector.
search_type_field = Field(
    title="Search type",
    content=search_type_select,
    description="Select if you want to search images by tags or text.",
)

# Generate tag search type selector.
tags_type_select = Select(
    items=[Select.Item(value=type, label=type.capitalize()) for type in g.TAGS_TYPES]
)

# Field for tag search type selector.
tags_type_field = Field(
    title="Tag search mode",
    content=tags_type_select,
    description="If 'Any' is selected, the search will return images with any of the tags. "
    "If 'All' is selected, the search will return only images which contain all of the tags.",
)
tags_type_field.hide()

# Field for search query input.
search_query_input = Input(minlength=1, placeholder="Enter the search query")
search_query_field = Field(
    title="Search query",
    content=Container(
        widgets=[search_query_input],
        direction="vertical",
    ),
    description="If using tags search mode, enter tags separated by commas. "
    "Otherwise, enter the text to search.",
)

# Generate license type selector.
license_items = []
for key, value in g.LICENSE_TYPES.items():
    license_items.append(Select.Item(value=value, label=key))
select_license = Select(items=license_items, multiple=True)

license_message = Text(status="error", text="License type is not selected.")
license_message.hide()

# Field for license type selector and license message.
license_field = Field(
    title="License types",
    description="At least one license must be selected.",
    content=Container(widgets=[select_license, license_message], direction="vertical"),
)

search_button = Button("Check number of images")

search_results = Text(status="info")
search_results.hide()

# Main card for all input widgets.
card = Card(
    title="2️⃣ Search method",
    description="How and what to find on Flickr.",
    content=Container(
        widgets=[
            search_type_field,
            tags_type_field,
            search_query_field,
            query_message,
            license_field,
            search_button,
            search_results,
        ],
        direction="vertical",
    ),
    lock_message="Please, enter API key and check the connection to the Flickr API.",
)
card.lock()


@search_button.click
def get_number_of_results():
    """Gets the number of images found by the search query."""
    query_message.hide()
    license_message.hide()

    search_query = search_query_input.get_value()
    license_type = select_license.get_value()
    license = ",".join([str(i) for i in license_type])

    sly.logger.debug(
        f"Button was clicked. Search query: {search_query}, license: {license}."
    )

    if search_query and license_type:
        # Getting the number of images found by the search query.
        search_type = search_type_select.get_value()
        tag_type = tags_type_select.get_value()

        params = g.PARAMS.copy()

        params.update(
            {
                "api_key": keys.flickr_api_key,
                search_type: search_query,
                "license": license,
                "per_page": 1,
                "page": 1,
            }
        )

        if search_type == "tags":
            params["tag_mode"] = tag_type

        response = requests.get(g.FLICKR_API_URL, params=params)

        if response.status_code != 200 or response.json().get("stat") != "ok":
            sly.logger.error(
                f"Error while getting the number of images: {response.text}"
            )
            search_results.text = "Error while getting the number of images."
            search_results.status = "error"
            search_results.show()
            return

        number_of_results = response.json().get("photos").get("total")

        sly.logger.debug(
            f"Search type: {search_type}, tag type: {tag_type}, search query: {search_query}, "
            f"license: {license}. Number of images found: {number_of_results}."
        )

        search_results.text = f"Number of images found: {number_of_results}."
        search_results.show()

    if not search_query:
        # Showing the error message if the search query is empty.
        query_message.show()

    if not license_type:
        # Showing the error message if the license type is not selected.
        license_message.show()


@search_type_select.value_changed
def change_search_type(search_type):
    sly.logger.debug(f"Search type was changed to {search_type}.")

    if search_type == "tags":
        tags_type_field.show()
    else:
        tags_type_field.hide()
