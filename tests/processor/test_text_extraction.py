"""Test code used for text extraction with easyocr."""

import cv2
import numpy as np
import pytest
from domsdatabasen._text_extraction import PDFTextReader
from PIL import Image


def read_image(image_path):
    """Read an image and convert it to grayscale if it is not already."""
    image = np.array(Image.open(image_path))
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


@pytest.fixture(scope="module")
def pdf_text_reader(config):
    """Return a PDFTextReader instance."""
    return PDFTextReader(config=config)


@pytest.mark.parametrize(
    "pdf_path, expected_text",
    [
        (
            "tests/data/processor/no_anonymization.pdf",
            "This is a PDF without anonymizations.",
        ),
        (
            "tests/data/processor/underlines.pdf",
            "Noget tekst hvor ord som er <anonym>understreget</anonym>\n"
            "vil blive anonymiseret",
        ),
    ],
)
def test_extract_text(pdf_text_reader, pdf_path, expected_text):
    """Test that text is extracted from a PDF."""
    pdf_data = pdf_text_reader.extract_text(pdf_path=pdf_path)
    text = pdf_text_reader._get_text_from_pages(pdf_data["pages"])
    assert text == expected_text


@pytest.mark.parametrize(
    "image_path, n_blobs_expected",
    [("tests/data/processor/blobs.png", 4)],
)
def test_get_blobs(pdf_text_reader, image_path, n_blobs_expected):
    """Test that blobs are found in an image."""
    binary_image = read_image(image_path)
    blobs = pdf_text_reader._get_blobs(binary_image)
    assert len(blobs) == n_blobs_expected


@pytest.mark.parametrize(
    "image_path, n_matches_expected",
    [
        ("tests/data/processor/underlines_1.png", 11),
        ("tests/data/processor/underlines_2.png", 2),
        ("tests/data/processor/underlines_3.png", 14),  # Case 96 page 6
        ("tests/data/processor/underlines_4.png", 36),  # Case 96 page 7
    ],
)
def test_line_anonymization_to_boxes(pdf_text_reader, image_path, n_matches_expected):
    """Test that underlines are found in an image."""
    image = read_image(image_path)
    anonymized_boxes, underlines = pdf_text_reader._line_anonymization_to_boxes(image)
    assert len(anonymized_boxes) == n_matches_expected
    assert len(underlines) == n_matches_expected


@pytest.mark.parametrize(
    "image_path, anonymized_boxes, underlines",
    [
        (
            "tests/data/processor/underlines_1.png",
            [{"coordinates": (0, 0, 15, 15)}],
            [(20, 20, 22, 30)],
        )
    ],
)
def test_process_image(pdf_text_reader, image_path, anonymized_boxes, underlines):
    """Test that an image is processed."""
    image = read_image(image_path)
    processed_image = pdf_text_reader._process_image(
        image=image,
        anonymized_boxes=anonymized_boxes,
        underlines=underlines,
    )
    assert isinstance(processed_image, np.ndarray)


@pytest.mark.parametrize(
    "boxes, text_expected",
    [
        (
            [
                {"coordinates": (0, 0, 30, 75), "text": "Hej"},
                {"coordinates": (80, 0, 110, 100), "text": "smukke"},
            ],
            "Hej\nsmukke",
        ),
        (
            [
                {"coordinates": (0, 0, 30, 75), "text": "Hej"},
                {"coordinates": (3100, 1300, 3125, 1350), "text": "smukke"},
            ],
            "Hej",
        ),
    ],
)
def test_get_text_from_boxes(pdf_text_reader, boxes, text_expected):
    """Test that text is extracted from boxes."""
    text = pdf_text_reader._get_text_from_boxes(boxes)
    assert text == text_expected


@pytest.mark.parametrize(
    "image_path, anonymized_box, invert, text_expected",
    [
        (
            "tests/data/processor/underlines_1.png",
            {"coordinates": (2863, 296, 2898, 490), "origin": "underline"},
            True,
            "<anonym>Tiltalte 2</anonym>",
        ),
        (
            "tests/data/processor/underlines_1.png",
            {"coordinates": (1186, 296, 1221, 490), "origin": "underline"},
            True,
            "<anonym>CPR nr. 1</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box.png",
            {"coordinates": [1007, 552, 1040, 583], "origin": "box"},
            False,
            "<anonym>Ø</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_2.png",
            {"coordinates": [1169, 274, 1213, 359], "origin": "underline"},
            True,
            "<anonym>By 1</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_3.png",
            {"coordinates": [886, 1945, 926, 2210], "origin": "box"},
            False,
            "<anonym>Person 5 (P5)</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_4.png",
            {"coordinates": [562, 1206, 624, 1673], "origin": "box"},
            False,
            "<anonym>Sagsøgte 2's</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_5.png",
            {"coordinates": [2439, 1338, 2488, 1555], "origin": "underline"},
            True,
            "<anonym>Tiltalte 5's</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_6.png",
            {"coordinates": [2359, 527, 2408, 1110], "origin": "underline"},
            True,
            "<anonym>Kærende 3 , tidligere Lejer 3</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_6.png",
            {"coordinates": [2870, 552, 2919, 1137], "origin": "underline"},
            True,
            "<anonym>Kærende 9 tidligere Lejer 9</anonym>",
        ),
        (
            ("tests/data/processor/get_text_from_box_7.png"),
            {"coordinates": [3016, 1063, 3065, 1159], "origin": "underline"},
            True,
            "<anonym>Navn</anonym>",
        ),
        (
            ("tests/data/processor/get_text_from_box_7.png"),
            {"coordinates": [3016, 389, 3065, 641], "origin": "underline"},
            True,
            "<anonym>Tiltaltelsigtede</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_8.png",
            {"coordinates": [1886, 1112, 1942, 1229], "origin": "box"},
            False,
            "<anonym>P1</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_9.png",
            {"coordinates": [474, 1440, 511, 1547], "origin": "box"},
            False,
            "<anonym>S</anonym>",
        ),
        (
            "tests/data/processor/get_text_from_box_9.png",
            {"coordinates": [820, 1842, 856, 1928], "origin": "box"},
            False,
            "",
        ),
    ],
)
def test_read_text_from_anonymized_box(
    pdf_text_reader, image_path, anonymized_box, invert, text_expected
):
    """Test that text is read from an anonymized box."""
    image = read_image(image_path)
    anonymized_box = pdf_text_reader._read_text_from_anonymized_box(
        image=image, anonymized_box=anonymized_box, invert=invert
    )
    assert anonymized_box["text"] == text_expected


@pytest.mark.parametrize(
    "image_path, n_matches_expected",
    [
        ("tests/data/processor/page_with_boxes_1.png", 4),
        ("tests/data/processor/page_with_stacked_boxes.png", 9),
        ("tests/data/processor/page_with_boxes_3.png", 6),
        ("tests/data/processor/page_with_boxes_4.png", 22),
        ("tests/data/processor/page_with_boxes_5.png", 4),
        ("tests/data/processor/page_with_boxes_6.png", 14),
        ("tests/data/processor/page_with_boxes_7.png", 29),  # Case 604
        ("tests/data/processor/page_with_boxes_8.png", 19),  # Case 555 page 1
        ("tests/data/processor/page_with_boxes_9.png", 11),  # Case 2508 page 1
        ("tests/data/processor/page_with_boxes_10.png", 19),  # Case 4 page 29
        ("tests/data/processor/page_with_boxes_11.png", 14),  # Case 32 page 2
        ("tests/data/processor/page_with_boxes_12.png", 9),  # Case 4 page 31
        ("tests/data/processor/page_with_boxes_13.png", 28),  # Case 44 page 2
    ],
)
def test_find_anonymized_boxes(pdf_text_reader, image_path, n_matches_expected):
    """Test that anonymized boxes are found in an image."""
    image = read_image(image_path)
    anonymized_boxes = pdf_text_reader._find_anonymized_boxes(image=image)
    assert len(anonymized_boxes) == n_matches_expected


@pytest.mark.parametrize(
    "image_path, binary_threshold",
    [
        ("tests/data/processor/boundary_noise_1.png", 200),
        ("tests/data/processor/boundary_noise_2.png", 200),
    ],
)
def test_remove_boundary_noise(pdf_text_reader, config, image_path, binary_threshold):
    """Test that boundary noise is removed from an image."""
    image = read_image(image_path)
    N, M = image.shape
    image_clean = pdf_text_reader._remove_boundary_noise(image.copy(), binary_threshold)
    assert (image_clean[:, 0] <= config.process.threshold_binarize_process_crop).all()
    assert (
        image_clean[:, M - 1] <= config.process.threshold_binarize_process_crop
    ).all()
    assert (image_clean[0, :] <= config.process.threshold_binarize_process_crop).all()
    assert (
        image_clean[N - 1, :] <= config.process.threshold_binarize_process_crop
    ).all()


@pytest.mark.parametrize(
    "image_path, n_splits_expected",
    [
        (
            "tests/data/processor/box_with_multiple_words_1.png",
            5,
        ),
        (
            "tests/data/processor/box_with_multiple_words_2.png",
            1,
        ),
    ],
)
def test_get_split_indices(pdf_text_reader, image_path, n_splits_expected):
    """Test that split indices are found in an image."""
    image = read_image(image_path)
    split = pdf_text_reader._get_split_indices(crop=image)
    assert len(split) == n_splits_expected


@pytest.mark.parametrize(
    "image_path, n_duplicates_expected",
    [
        (
            "tests/data/processor/double_underline.png",
            0,
        ),  # From e02382f, the smallest underline is now not found
    ],
)
def test_no_boxes_with_too_much_overlap(
    pdf_text_reader, image_path, n_duplicates_expected
):
    """Test that boxes with too much overlap are not found in an image."""
    image = read_image(image_path)
    (
        boxes,
        underlines,
    ) = pdf_text_reader._line_anonymization_to_boxes(image=image)

    assert len(underlines) - len(boxes) == n_duplicates_expected


@pytest.mark.parametrize(
    "image_path, difference_flag_expected",
    [
        ("tests/data/processor/page_with_logo.png", True),
        ("tests/data/processor/page_with_no_logo.png", False),
        ("tests/data/processor/page_with_center_logo.png", True),
    ],
)
def test_remove_logo(pdf_text_reader, image_path, difference_flag_expected):
    """Test that a logo is removed from an image."""
    image = read_image(image_path)
    image_without_logo = pdf_text_reader._remove_logo(image=image.copy())
    difference_flag = np.abs(image_without_logo - image).sum() > 0
    assert difference_flag == difference_flag_expected


@pytest.mark.parametrize(
    "image_path, n_tables_expected, texts_in_table_expected, invert, shape_expected",
    [
        (
            "tests/data/processor/image_processed_find_tables_1.png",
            1,
            ["Geografisk", "Medlemsstat", "Fiskeriart"],
            True,
            (4, 4),
        ),
        (
            "tests/data/processor/image_processed_find_tables_2.png",
            1,
            ["Eng.nr.", "Navn", "+500"],
            True,
            (2, 4),
        ),
        ("tests/data/processor/image_processed_with_no_tables.png", 0, [], True, None),
        (
            "tests/data/processor/page_with_table_1.png",
            1,
            ["DKK", "Indkomst før genoptagelse"],
            False,
            (4, 2),
        ),
    ],
)
def test_find_tables(
    pdf_text_reader,
    image_path,
    n_tables_expected,
    texts_in_table_expected,
    invert,
    shape_expected,
):
    """Test that tables are found in an image."""
    image = read_image(image_path)
    if invert:
        image = cv2.bitwise_not(image)
    table_boxes = pdf_text_reader._find_tables(image=image, read_tables=True)
    assert len(table_boxes) == n_tables_expected
    if n_tables_expected == 1:
        table = table_boxes[0]
        assert table["shape"] == shape_expected
        assert all(text in table["text"] for text in texts_in_table_expected)


@pytest.mark.parametrize(
    "image_path, rows_to_split_expected",
    [
        ("tests/data/processor/overlapping_boxes_1.png", [60]),
        ("tests/data/processor/overlapping_boxes_2.png", [62, 187, 122]),
        ("tests/data/processor/overlapping_boxes_3.png", [62, 122]),
        ("tests/data/processor/overlapping_boxes_4.png", [110, 56]),
    ],
)
def test_get_row_indices_to_split(pdf_text_reader, image_path, rows_to_split_expected):
    """Test that rows to split are found in an image."""
    image = read_image(image_path)
    rows_to_split = pdf_text_reader._get_row_indices_to_split(blob_image=image)
    assert rows_to_split == rows_to_split_expected


if __name__ == "__main__":
    pytest.main([__file__ + "::test_find_anonymized_boxes", "-s"])
