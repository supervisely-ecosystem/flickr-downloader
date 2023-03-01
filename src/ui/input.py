from supervisely.app.widgets import Input, InputNumber, Container, Card


search_query_input = Input(minlength=1, maxlength=50, placeholder="Search query")
images_number_input = InputNumber(value=1, min=1, precision=0)

search_query_card = Card(
    "Search query",
    "Enter the search query with length between 1 and 50 symbols",
    content=search_query_input,
)
images_number_card = Card(
    "Amount of images",
    "Enter the amount of images to download from Flickr",
    content=images_number_input,
)
container = Container(
    widgets=[search_query_card, images_number_card],
    direction="horizontal",
    fractions=[1, 1],
)
