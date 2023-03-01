from supervisely.app.widgets import Checkbox, Container, Card

import src.globals as g

checkboxes = {}
for key in g.OPTIONAL_METADATA_KEYS:
    checkboxes[key] = Checkbox(content=f"Image {key}")

card = Card(
    "Metadata fields",
    "Select metadata fields to add",
    content=Container(widgets=checkboxes.values(), direction="horizontal"),
)
