"""Reject invalid grid slice replacements before changing any image or GPU cell."""
import pytest

from pyglet.graphics import TextureGrid
from pyglet.image import ImageData, ImageGrid, ImageException


def image(value, width=1):
    return ImageData(width, 1, 'RGBA', bytes((value, value, value, 255)) * width)


@pytest.fixture(params=['image', 'texture'])
def grid(request, test_window):
    pixels = b''.join(bytes((value, value, value, 255)) for value in (10, 20, 30, 40))
    data = ImageData(2, 2, 'RGBA', pixels)
    if request.param == 'image':
        yield ImageGrid(data, 2, 2)
    else:
        texture = data.get_texture()
        yield TextureGrid(texture, 2, 2)
        texture.delete()


def values(grid):
    return [bytes(cell.get_image_data().get_bytes('RGBA', 4))[0] for cell in grid]


@pytest.mark.parametrize('selection', [slice(0, 2), slice(None, None, 2), slice((0, 0), (2, 1))])
@pytest.mark.parametrize('count', [0, 1, 3])
def test_slice_requires_one_image_per_selected_cell(grid, selection, count):
    before = values(grid)
    with pytest.raises(ValueError):
        grid[selection] = [image(100 + i) for i in range(count)]
    assert values(grid) == before


def test_all_dimensions_are_checked_before_any_cell_is_written(grid):
    before = values(grid)
    with pytest.raises(ImageException):
        grid[:2] = [image(100), image(110, width=2)]
    assert values(grid) == before


@pytest.mark.parametrize('selection,expected', [
    (slice(0, 2), [100, 110, 30, 40]),
    (slice(None, None, 2), [100, 20, 110, 40]),
    (slice((0, 0), (2, 1)), [100, 20, 110, 40]),
])
def test_valid_replacements_update_the_requested_cells(grid, selection, expected):
    grid[selection] = [image(100), image(110)]
    assert values(grid) == expected
    assert len(grid) == 4


def test_empty_selection_accepts_only_empty_replacements(grid):
    grid[0:0] = []
    assert values(grid) == [10, 20, 30, 40]
    with pytest.raises(ValueError):
        grid[0:0] = [image(100)]
    assert values(grid) == [10, 20, 30, 40]
