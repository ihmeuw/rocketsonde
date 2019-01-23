import os
import time
from multiprocessing import Process

from rocketsonde.core import Probe, basic_metric


def test_basic_usage__parent_only():
    monitor = Probe(basic_metric)
    monitor.start_monitor()

    pid = os.getpid()
    monitor.attach_to_process(pid)

    time.sleep(2)

    monitor.stop_monitor()

    records = monitor.records
    assert set(records.keys()) == {pid}
    assert len(records[pid]) > 0
    assert len(records[pid]) < 3


def test_basic_usage__children():
    def use_memory(amount):
        block = ["a"] * amount
        time.sleep(2)

    p = Process(target=use_memory, args=(1024 * 10000,))
    p.start()
    p2 = Process(target=use_memory, args=(1024 * 50000,))
    p2.start()

    monitor = Probe(basic_metric)
    monitor.start_monitor()

    pid = os.getpid()
    monitor.attach_to_process(p.pid)
    monitor.attach_to_process(p2.pid)

    p.join()
    p2.join()

    monitor.stop_monitor()

    records = monitor.records
    assert set(records.keys()) == {p.pid, p2.pid}
    assert len(records[p.pid]) > 0
    assert len(records[p2.pid]) > 0

    p_total = sum([r["rss"] for r in records[p.pid]])
    p2_total = sum([r["rss"] for r in records[p2.pid]])
    ratio = p2_total / p_total
    assert ratio > 3 and ratio < 10
