from supervisely.app.widgets import (
    Checkbox,
    Container,
    Card,
    Select,
    Text,
    RadioGroup,
    Field,
    InputNumber,
)

import src.globals as g

# Field for choosing starting number for searching images.
start_number_input = InputNumber(value=0, min=0, precision=0)
start_number_field = Field(
    title="Starting image number to search",
    description="From which image number to start the search.",
    content=start_number_input,
)

# Field for choosing the method of downloading images.
upload_method_radio = RadioGroup(
    items=[RadioGroup.Item(value=value) for value in g.DOWNLOAD_TYPES]
)
upload_method_field = Field(
    title="Choose the download method",
    description="Download links is faster, but it may cause data loss if the source file will be deleted.",
    content=upload_method_radio,
)

# Info text about blocked checkboxes.
owner_info_note = Text(
    status="info",
    text="Information about the owner of the image will be added to the "
    "metadata because it is a requirement of the license.",
)

# Generate blocked checkboxes for required metadata fields.
disabled_chekboxes = {}
for field in g.REQUIRED_METADATA_FIELDS:
    disabled_chekboxes[field] = Checkbox(content=f"Image {field}", checked=True)
for checkbox in disabled_chekboxes.values():
    checkbox.disable()
disabled_chekboxes_container = Container(
    widgets=disabled_chekboxes.values(), direction="vertical"
)

# Generate checkboxes for optional metadata fields.
checkboxes = {}
for field in g.OPTIONAL_METADATA_FIELDS:
    checkboxes[field] = Checkbox(content=f"Image {field}")
checkboxes_container = Container(widgets=checkboxes.values(), direction="vertical")

# Field for choosing image metadata fields to add.
metadata_field = Field(
    title="Image metadata fields",
    description="Select metadata fields to add for downloaded images.",
    content=Container(
        widgets=[owner_info_note, disabled_chekboxes_container, checkboxes_container],
        direction="vertical",
    ),
)

# Generate license type selector.
license_items = []
for key, value in g.LICENSE_TYPES.items():
    license_items.append(Select.Item(value=value, label=key))
select_license = Select(items=license_items, multiple=True)

license_message = Text(status="error", text="License type is not selected.")
license_message.hide()

# Field for choosing license type.
select_license_field = Field(
    title="Select license type",
    description="At least one license must be selected.",
    content=Container(widgets=[select_license, license_message], direction="vertical"),
)

# Main card for all settings widgets.
card = Card(
    content=Container(
        widgets=[
            start_number_field,
            upload_method_field,
            metadata_field,
            select_license_field,
        ],
        direction="vertical",
    ),
)
