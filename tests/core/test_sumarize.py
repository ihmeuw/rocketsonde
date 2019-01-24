from rocketsonde.core.summarize import _measurement_period, basic_summarizer


def test_measurement_period():
    observations = [{"time": 100}, {"time": 500}, {"time": 200}, {"time": 200}, {"time": 300}, {"time": 400}]

    first_time, last_time = _measurement_period(observations)

    assert first_time == 100
    assert last_time == 500


def test_basic_summarizer__happy_path():
    records = {
        123: [{"time": 100, "rss": 1024}, {"time": 101, "rss": 1024}, {"time": 102, "rss": 2024}],
        124: [
            {"time": 101, "rss": 1024},
            {"time": 102, "rss": 2024},
            {"time": 103, "rss": 3024},
            {"time": 104, "rss": 2024},
        ],
    }

    summary = basic_summarizer(records)

    assert summary[123]["total_samples"] == 3
    assert summary[123]["start_time"] == 100
    assert summary[123]["end_time"] == 102
    assert summary[123]["mean_rss"] == (1024 + 1024 + 2024) / 3
    assert summary[123]["peak_rss"] == 2024

    assert summary[124]["total_samples"] == 4
    assert summary[124]["start_time"] == 101
    assert summary[124]["end_time"] == 104
    assert summary[124]["mean_rss"] == (1024 + 2024 + 3024 + 2024) / 4
    assert summary[124]["peak_rss"] == 3024
