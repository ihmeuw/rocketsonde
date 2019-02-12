import pytest

from time import sleep

from rocketsonde.core import Probe, basic_metric
from rocketsonde.core.probe import ALL_WRITTEN


def test_large_data_set():
    def test_remote(metric_func, pid_queue, record_queue):
        for _ in range(100_000):
            record_queue.put((123, 321, {}))
        record_queue.put(ALL_WRITTEN)

    monitor = Probe(basic_metric, worker_function=test_remote)
    monitor.start_monitor()
    sleep(0.1)
    monitor.stop_monitor()

    assert len(monitor.records[123]) == 100_000


def test_worker_function_signature():
    with pytest.raises(ValueError):
        Probe(basic_metric, worker_function=lambda: ())

    with pytest.raises(ValueError):
        Probe(basic_metric, worker_function=lambda a, b, c, d: ())


def test_metric_signature():
    with pytest.raises(ValueError):
        Probe(lambda: ())

    with pytest.raises(ValueError):
        Probe(lambda a, b: ())
