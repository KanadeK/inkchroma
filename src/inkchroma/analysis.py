from __future__ import annotations

import math
from pathlib import Path
from typing import cast

from PIL import Image, UnidentifiedImageError

from inkchroma.model import InputError, Profile, ProfilePoint, SampleSpec

Rgb = tuple[float, float, float]
Lab = tuple[float, float, float]


def srgb_to_lab(rgb: Rgb) -> Lab:
    """Convert an sRGB triplet in the 0..255 range to CIE Lab (D65)."""

    linear: list[float] = []
    for channel in rgb:
        normalized = channel / 255.0
        linear.append(
            normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = linear
    x = (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047
    y = 0.2126729 * red + 0.7151522 * green + 0.0721750 * blue
    z = (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883

    def pivot(value: float) -> float:
        return value ** (1.0 / 3.0) if value > 216 / 24389 else (841 / 108) * value + 4 / 29

    fx, fy, fz = pivot(x), pivot(y), pivot(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def _mean_row(image: Image.Image, y: int, spans: tuple[tuple[int, int], ...]) -> Rgb:
    red = green = blue = count = 0
    for x_start, x_end in spans:
        for x in range(x_start, x_end):
            pixel = cast(tuple[int, int, int], image.getpixel((x, y)))
            red += pixel[0]
            green += pixel[1]
            blue += pixel[2]
            count += 1
    return red / count, green / count, blue / count


def _point(
    rf: float,
    delta_l: float,
    delta_a: float,
    delta_b: float,
    rgb: Rgb,
) -> ProfilePoint:
    return ProfilePoint(
        rf=rf,
        delta_l=delta_l,
        delta_a=delta_a,
        delta_b=delta_b,
        strength=math.sqrt(delta_l**2 + delta_a**2 + delta_b**2),
        rgb=(round(rgb[0]), round(rgb[1]), round(rgb[2])),
    )


def _interpolate(left: ProfilePoint, right: ProfilePoint, ratio: float, rf: float) -> ProfilePoint:
    def blend(a: float, b: float) -> float:
        return a + (b - a) * ratio

    return _point(
        rf,
        blend(left.delta_l, right.delta_l),
        blend(left.delta_a, right.delta_a),
        blend(left.delta_b, right.delta_b),
        (
            blend(float(left.rgb[0]), float(right.rgb[0])),
            blend(float(left.rgb[1]), float(right.rgb[1])),
            blend(float(left.rgb[2]), float(right.rgb[2])),
        ),
    )


def _resample(points: list[ProfilePoint], count: int) -> list[ProfilePoint]:
    result: list[ProfilePoint] = []
    last = len(points) - 1
    for index in range(count):
        position = index * last / (count - 1)
        lower = math.floor(position)
        upper = min(lower + 1, last)
        result.append(
            _interpolate(
                points[lower],
                points[upper],
                position - lower,
                index / (count - 1),
            )
        )
    return result


def _smooth(points: list[ProfilePoint]) -> tuple[ProfilePoint, ...]:
    result: list[ProfilePoint] = []
    for index, current in enumerate(points):
        neighbors = points[max(0, index - 1) : min(len(points), index + 2)]
        divisor = float(len(neighbors))
        result.append(
            _point(
                current.rf,
                sum(point.delta_l for point in neighbors) / divisor,
                sum(point.delta_a for point in neighbors) / divisor,
                sum(point.delta_b for point in neighbors) / divisor,
                (
                    sum(float(point.rgb[0]) for point in neighbors) / divisor,
                    sum(float(point.rgb[1]) for point in neighbors) / divisor,
                    sum(float(point.rgb[2]) for point in neighbors) / divisor,
                ),
            )
        )
    return tuple(result)


def _decode(path: Path, name: str) -> Image.Image:
    try:
        with Image.open(path) as source:
            return source.convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise InputError(
            f"sample '{name}': cannot decode image '{path.name}'; export it as PNG or JPEG"
        ) from error


def extract_profile(
    sample: SampleSpec,
    *,
    profile_points: int,
    minimum_signal: float,
) -> Profile:
    image = _decode(sample.image, sample.name)
    width, height = image.size
    if sample.lane.x_end > width or sample.origin_y >= height:
        raise InputError(
            f"sample '{sample.name}': lane or row coordinates exceed the {width}x{height} image; "
            "fix the coordinates or use the intended image"
        )
    if sample.lane.x_start < 2 or width - sample.lane.x_end < 2:
        raise InputError(
            f"sample '{sample.name}': the lane needs at least two paper pixels on each side; "
            "crop wider or narrow the lane"
        )

    raw: list[ProfilePoint] = []
    row_count = sample.origin_y - sample.solvent_front_y
    for row_index, y in enumerate(range(sample.origin_y, sample.solvent_front_y - 1, -1)):
        lane_rgb = _mean_row(image, y, ((sample.lane.x_start, sample.lane.x_end),))
        paper_rgb = _mean_row(
            image,
            y,
            ((0, sample.lane.x_start), (sample.lane.x_end, width)),
        )
        lane_lab = srgb_to_lab(lane_rgb)
        paper_lab = srgb_to_lab(paper_rgb)
        raw.append(
            _point(
                row_index / row_count,
                lane_lab[0] - paper_lab[0],
                lane_lab[1] - paper_lab[1],
                lane_lab[2] - paper_lab[2],
                lane_rgb,
            )
        )

    points = _smooth(_resample(raw, profile_points))
    peak_signal = max(point.strength for point in points)
    if peak_signal < minimum_signal:
        raise InputError(
            f"sample '{sample.name}': no measurable ink signal (peak Delta E {peak_signal:.2f} < "
            f"{minimum_signal:.2f}); rescan or lower minimum_signal_delta_e; use more contrast "
            "when rescanning"
        )
    return Profile(name=sample.name, points=points, peak_signal=peak_signal)
