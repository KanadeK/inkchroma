from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from inkchroma.analysis import analyze_project, compare_profiles, extract_profile, srgb_to_lab
from inkchroma.model import InputError, LaneSpec, Profile, ProfilePoint, Project, SampleSpec


def save_strip(
    path: Path,
    *,
    size: tuple[int, int] = (60, 120),
    bands: tuple[tuple[int, int, tuple[int, int, int]], ...] = (),
) -> None:
    image = Image.new("RGB", size, (242, 239, 229))
    draw = ImageDraw.Draw(image)
    for y_start, y_end, color in bands:
        draw.rectangle((20, y_start, 39, y_end), fill=color)
    image.save(path)


def sample(path: Path, *, origin_y: int = 110) -> SampleSpec:
    return SampleSpec(
        name="blue-a",
        image=path,
        lane=LaneSpec(x_start=20, x_end=40),
        solvent_front_y=10,
        origin_y=origin_y,
    )


def test_srgb_to_lab_matches_reference_primary_values() -> None:
    white = srgb_to_lab((255.0, 255.0, 255.0))
    red = srgb_to_lab((255.0, 0.0, 0.0))

    assert white == pytest.approx((100.0, 0.0, 0.0), abs=0.02)
    assert red == pytest.approx((53.24, 80.09, 67.20), abs=0.08)


def test_extract_profile_decodes_image_and_resamples_real_pixels(tmp_path: Path) -> None:
    image_path = tmp_path / "blue.png"
    save_strip(
        image_path,
        bands=(
            (30, 50, (82, 74, 164)),
            (72, 84, (42, 103, 162)),
        ),
    )

    profile = extract_profile(sample(image_path), profile_points=64, minimum_signal=2.0)

    assert profile.name == "blue-a"
    assert len(profile.points) == 64
    assert profile.points[0].rf == 0.0
    assert profile.points[-1].rf == 1.0
    strongest = max(profile.points, key=lambda point: point.strength)
    assert strongest.rf == pytest.approx(0.70, abs=0.12)
    assert profile.peak_signal > 20


def test_extract_profile_summarizes_separate_signal_bands(tmp_path: Path) -> None:
    image_path = tmp_path / "two-bands.png"
    save_strip(
        image_path,
        bands=(
            (30, 46, (82, 74, 164)),
            (76, 86, (42, 103, 162)),
        ),
    )

    profile = extract_profile(sample(image_path), profile_points=96, minimum_signal=2.0)

    assert len(profile.bands) == 2
    assert [band.rf_center for band in profile.bands] == pytest.approx([0.29, 0.72], abs=0.08)
    assert all(band.rf_start <= band.rf_center <= band.rf_end for band in profile.bands)
    assert all(band.peak_signal >= 2.0 for band in profile.bands)


def profile(name: str, values: tuple[float, ...]) -> Profile:
    points = tuple(
        ProfilePoint(
            rf=index / (len(values) - 1),
            delta_l=value,
            delta_a=0.0,
            delta_b=0.0,
            strength=abs(value),
            rgb=(80, 90, 150),
        )
        for index, value in enumerate(values)
    )
    return Profile(name=name, points=points, peak_signal=max(map(abs, values)), bands=())


def test_compare_profiles_reports_right_index_shift() -> None:
    left = profile("left", (0.0, 0.0, 8.0, 3.0, 0.0, 0.0))
    right = profile("right", (0.0, 0.0, 0.0, 8.0, 3.0, 0.0))

    comparison = compare_profiles(left, right, max_shift=2)

    assert comparison.distance == pytest.approx(0.0)
    assert comparison.right_index_shift == 1


def test_analyze_project_ranks_related_samples_before_different_ink(tmp_path: Path) -> None:
    blue_a_path = tmp_path / "blue-a.png"
    blue_b_path = tmp_path / "blue-b.png"
    green_path = tmp_path / "green.png"
    save_strip(blue_a_path, bands=((42, 62, (45, 76, 155)),))
    save_strip(blue_b_path, bands=((43, 63, (48, 78, 152)),))
    save_strip(green_path, bands=((42, 62, (47, 132, 78)),))

    def named_sample(name: str, image: Path) -> SampleSpec:
        return SampleSpec(
            name=name,
            image=image,
            lane=LaneSpec(x_start=20, x_end=40),
            solvent_front_y=10,
            origin_y=110,
        )

    project = Project(
        profile_points=64,
        minimum_signal_delta_e=2.0,
        samples=(
            named_sample("blue-a", blue_a_path),
            named_sample("blue-b", blue_b_path),
            named_sample("green", green_path),
        ),
    )

    result = analyze_project(project)

    assert [profile.name for profile in result.profiles] == ["blue-a", "blue-b", "green"]
    assert (result.comparisons[0].left, result.comparisons[0].right) == (
        "blue-a",
        "blue-b",
    )
    assert result.comparisons[0].distance < result.comparisons[1].distance


def test_analyze_project_orders_tied_pairs_by_sample_name(tmp_path: Path) -> None:
    image_path = tmp_path / "same.png"
    save_strip(image_path, bands=((42, 62, (45, 76, 155)),))

    def named_sample(name: str) -> SampleSpec:
        return SampleSpec(
            name=name,
            image=image_path,
            lane=LaneSpec(x_start=20, x_end=40),
            solvent_front_y=10,
            origin_y=110,
        )

    project = Project(
        profile_points=32,
        minimum_signal_delta_e=2.0,
        samples=tuple(named_sample(name) for name in ("zeta", "alpha", "middle")),
    )

    result = analyze_project(project)

    assert [(pair.left, pair.right) for pair in result.comparisons] == [
        ("alpha", "middle"),
        ("alpha", "zeta"),
        ("middle", "zeta"),
    ]


def test_extract_profile_normalizes_different_image_heights(tmp_path: Path) -> None:
    short_path = tmp_path / "short.png"
    tall_path = tmp_path / "tall.png"
    save_strip(short_path, bands=((45, 55, (50, 90, 150)),))
    save_strip(tall_path, size=(60, 180), bands=((80, 96, (50, 90, 150)),))

    short = extract_profile(sample(short_path), profile_points=48, minimum_signal=2.0)
    tall = extract_profile(sample(tall_path, origin_y=170), profile_points=48, minimum_signal=2.0)

    assert len(short.points) == len(tall.points) == 48
    assert short.points[-1].rf == tall.points[-1].rf == 1.0


def test_extract_profile_rejects_blank_strip_with_repair(tmp_path: Path) -> None:
    image_path = tmp_path / "blank.png"
    save_strip(image_path)

    with pytest.raises(
        InputError,
        match=r"sample 'blue-a'.*no measurable ink signal.*rescan or lower",
    ):
        extract_profile(sample(image_path), profile_points=64, minimum_signal=2.0)


def test_extract_profile_rejects_lane_without_paper_on_both_sides(tmp_path: Path) -> None:
    image_path = tmp_path / "blue.png"
    save_strip(image_path, bands=((30, 50, (82, 74, 164)),))
    invalid = SampleSpec(
        name="edge-lane",
        image=image_path,
        lane=LaneSpec(x_start=1, x_end=40),
        solvent_front_y=10,
        origin_y=110,
    )

    with pytest.raises(
        InputError,
        match=r"sample 'edge-lane'.*two paper pixels on each side.*crop wider",
    ):
        extract_profile(invalid, profile_points=64, minimum_signal=2.0)


def test_extract_profile_names_undecodable_image(tmp_path: Path) -> None:
    image_path = tmp_path / "broken.png"
    image_path.write_bytes(b"not a PNG")

    with pytest.raises(
        InputError,
        match=r"sample 'blue-a'.*cannot decode.*export it as PNG or JPEG",
    ):
        extract_profile(sample(image_path), profile_points=64, minimum_signal=2.0)
