import re

def validate_size(value: str):
    m = re.fullmatch(r"(\d+)x(\d+)", value.strip())
    if not m:
        raise ValueError("Resolution must be WIDTHxHEIGHT, e.g. 3840x2160.")
    w, h = map(int, m.groups())
    if w % 16 or h % 16:
        raise ValueError("Width and height must be divisible by 16.")
    ratio = w / h
    if not (1/3 <= ratio <= 3):
        raise ValueError("Aspect ratio must be between 1:3 and 3:1.")
    pixels = w * h
    if w > 3840 or h > 3840:
        raise ValueError("Neither edge may exceed 3840 px.")
    if not (655_360 <= pixels <= 8_294_400):
        raise ValueError("Pixel count must be between 655,360 and 8,294,400.")
    return w, h

def validate_options(model, quality, output_format):
    if model == "gpt-image-2" and quality in ("xhigh", "max"):
        raise ValueError("gpt-image-2 does not support xhigh/max.")
    if output_format not in ("png", "jpeg", "webp"):
        raise ValueError("Unsupported output format.")
