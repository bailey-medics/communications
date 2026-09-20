def clean_client_data(
    data: dict[str, list[str]],
) -> dict[str, str | list[str]]:
    cleaned_data = {}
    for key, value in data.items():
        if key == "selected_clients[]":
            cleaned_data[key] = value
        elif (key == "short_blurb" or key == "long_blurb") and data[
            "hyperlink"
        ]:
            cleaned_data[key] = f"{value[0]} { data['hyperlink'][0]}"
        else:
            cleaned_data[key] = value[0]
    return cleaned_data
