import flickr_api

from supervisely.app.widgets import Input, Card, Button, Container, Text

import src.ui.output as output


key_input = Input(minlength=32, maxlength=32, input_type="password")
check_key_button = Button("Check connection")
check_result = Text()
check_result.hide()


card = Card(
    "Flickr API key",
    "Please, enter your Flickr API key.",
    content=Container(
        widgets=[key_input, check_key_button, check_result], direction="vertical"
    ),
)


@check_key_button.click
def connect_to_flickr():
    check_result.hide()

    flickr_api_key = key_input.get_value()
    flickr_api.set_keys(flickr_api_key, "placeholder")

    try:
        flickr_api.test.echo()
        connection = True
    except Exception:
        connection = False

    if not connection:
        check_result.text = "The connection to the Flickr API failed, check the key."
        check_result.status = "error"
        check_result.show()
        return

    check_result.text = "The connection to the Flickr API was successful."
    check_result.status = "success"
    check_result.show()

    key_input.disable()
    check_key_button.hide()

    output.download_button.enable()
