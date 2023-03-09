import flickr_api
import supervisely as sly

from supervisely.app.widgets import Input, Card, Button, Container, Text

import src.ui.output as output
import src.ui.input as input
import src.ui.settings as settings
import src.globals as g


key_input = Input(type="password")
file_loaded_info = Text(
    text="The API key was loaded from the team files.", status="info"
)
file_loaded_info.hide()

check_key_button = Button("Check connection")
check_result = Text()
check_result.hide()

card = Card(
    "Flickr API key",
    "Please, enter your Flickr API key.",
    content=Container(
        widgets=[key_input, check_key_button, file_loaded_info, check_result],
        direction="vertical",
    ),
)


@check_key_button.click
def connect_to_flickr():
    """Checks the connection to the Flickr API with the global API key."""
    check_result.hide()

    global flickr_api_key
    if not flickr_api_key:
        flickr_api_key = key_input.get_value()

    # API secret is not required for, so using a placeholder.
    flickr_api.set_keys(flickr_api_key, "placeholder")

    try:
        # Checking the connection to the Flickr API with specified API key.
        flickr_api.test.echo()
        sly.logger.info("The connection to the Flickr API was successful.")
    except Exception as error:
        # Resetting the global API key if the connection failed.
        flickr_api_key = None
        sly.logger.warning(
            f"The connection to the Flickr API failed with error: {error}."
        )
        check_result.text = "The connection to the Flickr API failed, check the key."
        check_result.status = "error"
        check_result.show()
        return

    check_result.text = "The connection to the Flickr API was successful."
    check_result.status = "success"
    check_result.show()

    # Disabling fields for entering API key if the connection was successful.
    key_input.disable()
    check_key_button.hide()

    # Unlocking all cards if the connection was successful.
    input.card.unlock()
    output.card.unlock()
    settings.card.unlock()


global flickr_api_key
flickr_api_key = g.key_from_file()
if flickr_api_key:
    # If the API key was loaded from the team files, launching the connection check.
    check_key_button.click(connect_to_flickr())
    key_input.hide()
    file_loaded_info.show()
