from supervisely.app.widgets import (
    Input,
    InputNumber,
    Container,
    Card,
    Text,
    Field,
    Button,
)

import src.ui.settings as settings
import src.ui.keys as keys

search_query_input = Input(minlength=1, placeholder="Enter the search query")
images_number_input = InputNumber(value=1, min=1, precision=0)
query_message = Text(status="error", text="Please, enter the search query.")
query_message.hide()

search_button = Button("Check number of images")
search_results = Text(status="info")
search_results.hide()

# Field for entering search query.
search_query_field = Field(
    title="Image search query",
    description="What to find on Flickr.",
    content=search_query_input,
)

# Field for choosing number of images to find.
images_number_field = Field(
    title="Number of images",
    description="How many images to find on Flickr.",
    content=images_number_input,
)

# Main card for all input widgets.
card = Card(
    content=Container(
        widgets=[
            search_query_field,
            search_button,
            search_results,
            query_message,
            images_number_field,
        ],
        direction="vertical",
    ),
    lock_message="Please, enter API key and check the connection to the Flickr API.",
)
card.lock()


@search_button.click
def get_number_of_results():
    """Gets the number of images found by the search query."""
    search_query = search_query_input.get_value()
    if not search_query:
        # Showing the error message if the search query is empty.
        search_results.text = "Please, enter the search query."
        search_results.status = "error"
        search_results.show()
        return

    license_type = settings.select_license.get_value()
    if not license_type:
        # Showing the error message if the license type is not selected.
        search_results.text = "License type is not selected."
        search_results.status = "error"
        search_results.show()
        return

    # Getting the number of images found by the search query.
    number_of_results = keys.flickr_api.Photo.search(
        text=search_query, license=license_type, per_page=1, page=1
    ).info.total

    search_results.text = f"Number of images found: {number_of_results}."
    search_results.show()
