# GPT Image token rates used when the API returns usage.
# Keep isolated here so pricing changes can be updated without touching UI/API code.
RATES = {
    "gpt-image-2.5-sunburst": {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0},
    "gpt-image-2.5-flare": {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0},
}

def calculate_cost(model, usage):
    rates = RATES.get(model)
    if not rates or not usage:
        return None
    details = usage.get("input_tokens_details") or {}
    text_in = details.get("text_tokens")
    image_in = details.get("image_tokens")
    out = usage.get("output_tokens")
    if text_in is None or image_in is None or out is None:
        return None
    return (text_in*rates["text_in"] + image_in*rates["image_in"] + out*rates["image_out"]) / 1_000_000
