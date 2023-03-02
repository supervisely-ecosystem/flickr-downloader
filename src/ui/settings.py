from supervisely.app.widgets import Checkbox, Container, Card

import src.globals as g

# Generate checkboxes for metadata fields.
checkboxes = {}
for key in g.OPTIONAL_METADATA_KEYS:
    checkboxes[key] = Checkbox(content=f"Image {key}")

card = Card(
    "Images metadata fields",
    "Select metadata fields to add for downloaded images.",
    content=Container(widgets=checkboxes.values(), direction="horizontal"),
)
