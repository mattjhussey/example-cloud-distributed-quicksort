"""Test the basic functionality of the distributed quicksort."""

import pytest
from example_cloud_distributed_quicksort.main import quicksort_distributed


@pytest.mark.asyncio
async def test_quicksort_empty_list() -> None:
    """Test quicksort with empty list."""
    result = await quicksort_distributed([])
    assert result == []


@pytest.mark.asyncio
async def test_quicksort_single_element() -> None:
    """Test quicksort with single element."""
    result = await quicksort_distributed([42])
    assert result == [42]


@pytest.mark.asyncio
async def test_quicksort_multiple_elements() -> None:
    """Test quicksort with multiple elements."""
    input_data = [64, 34, 25, 12, 22, 11, 90]
    expected = [11, 12, 22, 25, 34, 64, 90]
    result = await quicksort_distributed(input_data)
    assert result == expected


@pytest.mark.asyncio
async def test_quicksort_already_sorted() -> None:
    """Test quicksort with already sorted list."""
    input_data = [1, 2, 3, 4, 5]
    expected = [1, 2, 3, 4, 5]
    result = await quicksort_distributed(input_data)
    assert result == expected


@pytest.mark.asyncio
async def test_quicksort_reverse_sorted() -> None:
    """Test quicksort with reverse sorted list."""
    input_data = [5, 4, 3, 2, 1]
    expected = [1, 2, 3, 4, 5]
    result = await quicksort_distributed(input_data)
    assert result == expected


@pytest.mark.asyncio
async def test_quicksort_duplicates() -> None:
    """Test quicksort with duplicate values."""
    input_data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
    expected = [1, 1, 2, 3, 3, 4, 5, 5, 6, 9]
    result = await quicksort_distributed(input_data)
    assert result == expected
