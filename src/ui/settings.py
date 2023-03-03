from supervisely.app.widgets import Checkbox, Container, Card, Select, Text

import src.globals as g

# Generate checkboxes for metadata fields.
checkboxes = {}
for key in g.OPTIONAL_METADATA_KEYS:
    checkboxes[key] = Checkbox(content=f"Image {key}")

license_items = []
for key, value in g.LICENSE_TYPES.items():
    license_items.append(Select.Item(value=value, label=key))

select_license_text = Text(text="Select license type:")
select_license = Select(items=license_items)

owner_info_note = Text(
    status="info",
    text="Information about the owner of the image will be added to the "
    "metadata because it is a requirement of the license.",
)
checkboxes_container = Container(widgets=checkboxes.values(), direction="vertical")


card = Card(
    "Image metadata fields",
    "Select metadata fields to add for downloaded images.",
    content=Container(
        widgets=[
            checkboxes_container,
            select_license_text,
            select_license,
            owner_info_note,
        ]
    ),
)
