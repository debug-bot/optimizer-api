from data.frontend_data import data
from data.filter_units import filter_units
from data.constraints import constraints_data
from data.esg_constraints import esg_constraints_data

print("============== loading... ===============")

flt_data_to_update = data["fltValue"]["selectedData"]


def update_units_flt(selected_data_to_update, filter_units):

    for selected_item in selected_data_to_update:
        for unit in filter_units:
            if unit["id"] == selected_item["id"]:
                unit["value"] = selected_item["value"]
                break
    return filter_units


filter_units_updated = update_units_flt(flt_data_to_update, filter_units)


def update_units_cons(original_units, units_to_update):

    for group_index, group in enumerate(units_to_update):
        for new_unit in group:
            # Find and replace the corresponding unit in 'original_units'
            for unit in original_units[group_index]:
                if unit["id"] == new_unit["id"]:
                    unit["value"] = new_unit["value"]
                    break
    return original_units


# Example usage
updated_units_cons = update_units_cons(constraints_data["units"], data["consValue"])
updated_units_esg_cons = update_units_cons(
    esg_constraints_data["units"], data["esgconsValue"]
)


matrics = {
    "MaxMin": data["objValue"]["action"],
    "Objet": data["objValue"]["unit"],
    "salesbuys": data["objValue"]["fieldOne"],
    "portfolio": tuple(data["objValue"]["fieldTwo"]),
    "solver": data["prmValue"]["solver"],
    "size": updated_units_cons[0][0]["value"][0],
    "Yield_lower": updated_units_cons[0][3]["value"][0],
    "Yield_upper": updated_units_cons[0][3]["value"][1],
    "Spread_lower": updated_units_cons[0][4]["value"][0],
    "Spread_upper": updated_units_cons[0][4]["value"][1],
    "Duration_lower": updated_units_cons[0][5]["value"][0],
    "Duration_upper": updated_units_cons[0][5]["value"][1],
    "Maturity_lower": updated_units_cons[0][6]["value"][0],
    "Maturity_upper": updated_units_cons[0][6]["value"][1],
    "SCR_lower": updated_units_cons[0][7]["value"][0],
    "SCR_upper": updated_units_cons[0][7]["value"][1],
    "ESG_SCORE_lower": updated_units_esg_cons[0][0]["value"][0],
    "ESG_SCORE_upper": updated_units_esg_cons[0][0]["value"][1],
    "CI_lower": updated_units_esg_cons[0][1]["value"][0],
    "CI_upper": updated_units_esg_cons[0][1]["value"][1],
    "Decarb_lower": updated_units_esg_cons[0][2]["value"][0],
    "Decarb_upper": updated_units_esg_cons[0][2]["value"][1],
    "Warf_lower": updated_units_cons[0][8]["value"][0],
    "Warf_upper": updated_units_cons[0][8]["value"][1],
    "PnL_lower": updated_units_cons[0][9]["value"][0],
    "PnL_upper": updated_units_cons[0][9]["value"][1],
    "weight_lower": updated_units_cons[0][10]["value"][0],
    "weight_upper": updated_units_cons[0][10]["value"][1],
    "recommendation": data["prmValue"]["checks"],
    "turnover": updated_units_cons[0][2]["value"],
    "nonzero": updated_units_cons[0][1]["value"][0],
    "unit": data["prmValue"]["unit"],
    "fixed_size": data["prmValue"]["fixedSize"],
}


def convert_to_filters_metrics(filter_units_updated):
    filters_metrics = {}
    for unit in filter_units_updated:
        # Extracting the name and modifying it as per requirements
        name = unit["name"].split(",")[0].replace(" ", "_")
        # Extracting the values
        lower_value, upper_value = unit["value"]

        # Adding the lower and upper filters to the dictionary
        filters_metrics[f"{name}_lower_filter"] = lower_value
        filters_metrics[f"{name}_upper_filter"] = upper_value
    return filters_metrics


def convert_to_filters_groups(checkboxes_data):
    filters_groups = {}
    for category, checkboxes in checkboxes_data.items():
        # Adding '_filter' to the category name and making it title case (e.g. 'sectors' -> 'Sectors_filter')
        category_key = category.title() + "_filter"
        items = {checkbox["label"]: checkbox["checked"] for checkbox in checkboxes}
        filters_groups[category_key] = items
    return filters_groups


def convert_to_buffer_data(constraints_data):
    buffer_data = {}

    for name, units in zip(constraints_data["names"], constraints_data["units"]):
        # Construct buffer name, e.g., "buffer_Sectors"
        buffer_name = f"buffer_{name}"
        buffer_values = {unit["name"]: unit["value"][0] for unit in units}

        buffer_data[buffer_name] = buffer_values

    return buffer_data


# Convert the constraints_data to buffer data format
buffer_data_converted = convert_to_buffer_data(constraints_data)

# Convert the checkboxes_data back to filters_groups format
converted_filters_matrics = convert_to_filters_metrics(filter_units_updated)
converted_filters_groups = convert_to_filters_groups(data["fltValue"]["checkboxes"])


# Specify the file path and name
file_path = "f:/fiverr_project/python notebook/optimizer-api/mydata/output.py"

# Open the file in write mode
with open(file_path, "w") as file:
    # Write the variables to the file
    file.write(f"matrics = {matrics}\n")
    file.write(f"buffers = {buffer_data_converted}\n")
    file.write(f"filters_matrics = {converted_filters_matrics}\n")
    file.write(f"filters_groups = {converted_filters_groups}\n")

# Print a message indicating that the file has been saved
print(f"Variables saved to {file_path}")
