from supervisely.app.widgets import Input, Container, Card, Text, Field, Button, Select

import src.ui.keys as keys
import src.globals as g

search_query_input = Input(minlength=1, placeholder="Enter the search query")
query_message = Text(status="error", text="Please, enter the search query.")
query_message.hide()

search_button = Button("Check number of images")
search_results = Text(status="info")
search_results.hide()

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


# Main card for all input widgets.
card = Card(
    title="2️⃣ Search query",
    description="What to find on Flickr.",
    content=Container(
        widgets=[
            search_query_input,
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

    if search_query and license_type:
        # Getting the number of images found by the search query.
        number_of_results = keys.flickr_api.Photo.search(
            text=search_query, license=license_type, per_page=1, page=1
        ).info.total

        search_results.text = f"Number of images found: {number_of_results}."
        search_results.show()

    if not search_query:
        # Showing the error message if the search query is empty.
        query_message.show()

    if not license_type:
        # Showing the error message if the license type is not selected.
        license_message.show()
