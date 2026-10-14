from autolabeler.ingest import normalize_text, split_page


def test_split_preserves_bounds_and_overlap():
    text = normalize_text("First paragraph has useful evidence.\n\nSecond paragraph has more detail. " * 8)
    chunks = list(split_page(text, max_chars=100, overlap_chars=15))
    assert len(chunks) > 1
    assert all(0 <= start < end <= len(text) for start, end, _ in chunks)
    assert all(end - start <= 100 for start, end, _ in chunks)
    assert chunks[1][0] < chunks[0][1]


def test_split_rejects_invalid_overlap():
    try:
        list(split_page("text", 10, 10))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
