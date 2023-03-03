from supervisely.app.widgets import Input, InputNumber, Container, Card


search_query_input = Input(minlength=1, placeholder="Enter the search query")
images_number_input = InputNumber(value=1, min=1, precision=0)

search_query_card = Card(
    "Image search query",
    "What to find on Flickr.",
    content=search_query_input,
)
images_number_card = Card(
    "Number of images",
    "How many images to find on Flickr.",
    content=images_number_input,
)
container = Container(
    widgets=[search_query_card, images_number_card], direction="vertical"
)
