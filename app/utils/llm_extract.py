import re


def extract_content(text: str) -> dict:
    if text == "":
        raise ValueError("No text returned from ChatGPT")

    title_match = re.search(r"'''title:\s*(.*?)\s*'''", text, re.DOTALL)
    long_blurb_match = re.search(
        r"'''long_blurb:\s*(.*?)\s*'''", text, re.DOTALL
    )
    short_blurb_match = re.search(
        r"'''short_blurb:\s*(.*?)\s*'''", text, re.DOTALL
    )

    if not (title_match and long_blurb_match and short_blurb_match):
        raise ValueError(
            f"Returned content does not match expected format:</br></br>{text}"
        )

    title = title_match.group(1).strip() if title_match else ""
    long_blurb = long_blurb_match.group(1).strip() if long_blurb_match else ""
    short_blurb = (
        short_blurb_match.group(1).strip() if short_blurb_match else ""
    )

    return {
        "title": title,
        "long_blurb": long_blurb,
        "short_blurb": short_blurb,
    }
