import supervisely as sly

from supervisely.app.widgets import Container

import src.ui.input as input
import src.ui.settings as settings
import src.ui.output as output

layout = Container(widgets=[input.container, settings.container, output.card])

app = sly.Application(layout=layout)
