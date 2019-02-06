from time import sleep

from rocketsonde.core import Probe, basic_metric


def test_large_data_set():
    def test_remote(metric_func, pid_queue, record_queue, records_ready, shutdown_event):
        records_ready.set()
        for _ in range(100_000):
            record_queue.put((123, 321, {}))
        records_ready.clear()

    monitor = Probe(basic_metric, worker_function=test_remote)
    monitor.start_monitor()
    sleep(0.1)
    monitor.stop_monitor()

    assert len(monitor.records[123]) == 100_000
