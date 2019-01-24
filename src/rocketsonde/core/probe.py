from time import time
from multiprocessing import Process, Pipe, Event, Condition
from collections import defaultdict
import atexit


class _Worker:
    __slots__ = ["pid_pipe", "record_pipe", "dump_records_condition", "shutdown_event", "process"]

    def __init__(self, shutdown_event, pid_pipe, record_pipe, dump_records_condition, process):
        self.shutdown_event = shutdown_event
        self.pid_pipe = pid_pipe
        self.record_pipe = record_pipe
        self.dump_records_condition = dump_records_condition
        self.process = process


class Probe:
    __slots__ = ["_records", "_process_user_data", "_worker", "_metric"]

    def __init__(self, metric):
        self._metric = metric
        self._records = defaultdict(list)
        self._process_user_data = {}
        self._worker = None

    def attach_to_process(self, pid, data=None):
        if self._worker is None:
            raise ValueError("Cannot attach to process when not running")

        self._worker.pid_pipe.send(("add", pid))
        self._process_user_data[pid] = data

    def detach_from_process(self, pid):
        if self._worker is None:
            raise ValueError("Cannot detach from process when not running")

        self._worker.pid_pipe.send(("remove", pid))

    @property
    def records(self):
        if self._worker is not None:
            self._drain_record_pipe()
        return dict(self._records)

    def start_monitor(self):
        remote_pid_pipe, pid_pipe = Pipe(False)
        record_pipe, remote_record_pipe = Pipe(False)
        shutdown_event = Event()
        dump_records_condition = Condition()
        process = Process(
            target=_monitor,
            args=(self._metric, remote_pid_pipe, remote_record_pipe, dump_records_condition, shutdown_event),
        )

        process.start()
        atexit.register(self._panic_kill_monitor)

        self._worker = _Worker(
            shutdown_event=shutdown_event,
            pid_pipe=pid_pipe,
            record_pipe=record_pipe,
            dump_records_condition=dump_records_condition,
            process=process,
        )

    def _drain_record_pipe(self):
        if self._worker is not None:
            with self._worker.dump_records_condition:
                self._worker.dump_records_condition.notify()
                if self._worker.dump_records_condition.wait(3):
                    while self._worker.record_pipe.poll():
                        pid, timestamp, record = self._worker.record_pipe.recv()
                        self._records[pid].append({**{"time": timestamp}, **record})

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

        self._worker.shutdown_event.set()

        try:
            self._drain_record_pipe()
        except EOFError:
            # EOFError indicates that the record pipe is empty and the child has stopped, which is fine
            pass
        self._worker.process.join(timeout)
        atexit.unregister(self._panic_kill_monitor)

        if self._worker.process.exitcode is None:
            self._worker.process.kill()

        self._worker = None


def _monitor(metric_func, pid_pipe, record_pipe, dump_records_condition, shutdown_event):
    pids = set()
    last_sample = 0
    records = []
    while not shutdown_event.is_set():
        now = time()
        if now - last_sample > 1:
            last_sample = now
            while pid_pipe.poll():
                action, pid = pid_pipe.recv()
                if action == "add":
                    pids.add(pid)
                elif action == "remove":
                    pids.remove(pid)
                else:
                    raise ValueError(f"Unknown pid list action '{action}'")

            dead_pids = set()
            for pid in pids:
                record = metric_func(pid)
                if record is None:
                    dead_pids.add(pid)
                else:
                    records.append((pid, time(), record))
            pids = pids.difference(dead_pids)

        with dump_records_condition:
            if dump_records_condition.wait(0.25):
                for record in records:
                    record_pipe.send(record)
                records.clear()
                dump_records_condition.notify()
