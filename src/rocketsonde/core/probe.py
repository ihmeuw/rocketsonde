from time import time, sleep
from inspect import signature
from multiprocessing import Process, Queue
from collections import defaultdict
import atexit

SHUTDOWN = "shutdown"
ALL_WRITTEN = "all_written"


class _Worker:
    __slots__ = ["pid_queue", "record_queue", "process"]

    def __init__(self, pid_queue, record_queue, process):
        self.pid_queue = pid_queue
        self.record_queue = record_queue
        self.process = process


class Probe:
    __slots__ = ["_records", "_process_user_data", "_worker", "_metric", "_worker_function"]

    def __init__(self, metric, worker_function=None):
        self._metric = metric
        try:
            signature(self._metric).bind(123)
        except TypeError:
            raise ValueError("metric must accept one positional argument")

        self._worker_function = _monitor if worker_function is None else worker_function
        try:
            signature(self._worker_function).bind(1, 2, 3)
        except TypeError:
            raise ValueError("worker_function must accept three positional arguments")

        self._records = defaultdict(list)
        self._process_user_data = defaultdict(None)
        self._worker = None

    def attach_to_process(self, pid, data=None):
        if self._worker is None:
            raise ValueError("Cannot attach to process when not running")

        self._worker.pid_queue.put(("add", pid))
        self._process_user_data[pid] = data

    def detach_from_process(self, pid):
        if self._worker is None:
            raise ValueError("Cannot detach from process when not running")

        self._worker.pid_queue.put(("remove", pid))

    @property
    def records(self):
        if self._worker is not None:
            self._drain_record_pipe()
        return dict(self._records)

    def user_data(self, pid):
        return self._process_user_data[pid]

    def probe_pid(self):
        if self._worker is None:
            raise ValueError("Worker is not running")
        return self._worker.process.pid

    def start_monitor(self):
        pid_queue = Queue(100)
        record_queue = Queue(10000)
        process = Process(target=self._worker_function, args=(self._metric, pid_queue, record_queue))

        process.start()
        atexit.register(self._panic_kill_monitor)

        self._worker = _Worker(pid_queue=pid_queue, record_queue=record_queue, process=process)

    def _drain_record_pipe(self):
        if self._worker is not None:
            pipe_clean = False
            while (self._worker.process.is_alive() and not pipe_clean) or not self._worker.record_queue.empty():
                while not self._worker.record_queue.empty():
                    item = self._worker.record_queue.get()
                    if item == ALL_WRITTEN:
                        pipe_clean = True
                    else:
                        pipe_clean = False
                        pid, timestamp, record = item
                        self._records[pid].append({**{"time": timestamp}, **record})
                if not pipe_clean:
                    sleep(0.1)

    def _panic_kill_monitor(self):
        """This should only trigger when the parent exits without properly
        cleaning up by calling stop_monitor. We don't collect any data in
        this case, just make sure the child process get's killed.
        """
        if self._worker is not None:
            self._worker.process.kill()

    def stop_monitor(self, timeout=3):
        if self._worker is None:
            raise ValueError("Cannot stop when not running")

        self._worker.pid_queue.put(SHUTDOWN)

        self._drain_record_pipe()
        self._worker.process.join(timeout)
        atexit.unregister(self._panic_kill_monitor)

        if self._worker.process.exitcode is None:
            self._worker.process.kill()

        self._worker = None


def _dump_records(records, record_queue):
    while records and not record_queue.full():
        record = records.pop()
        record_queue.put(record)
    if not records:
        record_queue.put(ALL_WRITTEN)


def _monitor(metric_func, pid_queue, record_queue):
    pids = set()
    last_sample = 0
    records = []
    do_shutdown = False
    while not do_shutdown:
        now = time()
        if now - last_sample > 1:
            last_sample = now
            while not pid_queue.empty():
                item = pid_queue.get()
                if item == SHUTDOWN:
                    do_shutdown = True
                    break
                else:
                    action, pid = item
                    if action == "add":
                        pids.add(pid)
                    elif action == "remove":
                        pids.remove(pid)
                    else:
                        raise ValueError(f"Unknown pid list action '{action}'")

            if not do_shutdown:
                dead_pids = set()
                for pid in pids:
                    record = metric_func(pid)
                    if record is None:
                        dead_pids.add(pid)
                    else:
                        records.append((pid, time(), record))
                pids = pids.difference(dead_pids)

        _dump_records(records, record_queue)
        sleep(0.25)

    cleanup_start = time()
    while records and time() - cleanup_start < 5:
        _dump_records(records, record_queue)
        sleep(0.1)
