from supervisely.app.widgets import Input, InputNumber, Container, Card, Text, Field


search_query_input = Input(minlength=1, placeholder="Enter the search query")
images_number_input = InputNumber(value=1, min=1, precision=0)
query_message = Text(status="error", text="Please, enter the search query.")
query_message.hide()

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
        widgets=[search_query_field, query_message, images_number_field],
        direction="vertical",
    ),
)
