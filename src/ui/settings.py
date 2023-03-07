from supervisely.app.widgets import Checkbox, Container, Card, Select, Text, RadioGroup

import src.globals as g

upload_type = RadioGroup(
    items=[RadioGroup.Item(value=value) for value in g.DOWNLOAD_TYPES]
)
upload_type_card = Card(
    "Choose the download method",
    "Download links is faster, but it may cause data loss if the source file will be deleted.",
    content=upload_type,
)

# Generate checkboxes for metadata fields.
checkboxes = {}
for field in g.OPTIONAL_METADATA_FIELDS:
    checkboxes[field] = Checkbox(content=f"Image {field}")

blocked_chekboxes = {}
for field in g.REQUIRED_METADATA_FIELDS:
    blocked_chekboxes[field] = Checkbox(content=f"Image {field}", checked=True)
for checkbox in blocked_chekboxes.values():
    checkbox.disable()


license_items = []
for key, value in g.LICENSE_TYPES.items():
    license_items.append(Select.Item(value=value, label=key))

select_license_text = Text(text="Select license type:")
select_license = Select(items=license_items, multiple=True)

license_message = Text(status="error", text="License type is not selected.")
license_message.hide()

owner_info_note = Text(
    status="info",
    text="Information about the owner of the image will be added to the "
    "metadata because it is a requirement of the license.",
)
checkboxes_container = Container(widgets=checkboxes.values(), direction="vertical")
blocked_chekboxes_container = Container(
    widgets=blocked_chekboxes.values(), direction="vertical"
)

metadata_card = Card(
    "Image metadata fields",
    "Select metadata fields to add for downloaded images.",
    content=Container(
        widgets=[
            owner_info_note,
            blocked_chekboxes_container,
            checkboxes_container,
            select_license_text,
            select_license,
            license_message,
        ]
    ),
)

container = Container(widgets=[upload_type_card, metadata_card], direction="vertical")
