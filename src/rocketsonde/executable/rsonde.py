import json
import argparse
import sys
import subprocess
from time import sleep

import psutil

from rocketsonde.core.probe import Probe
from rocketsonde.core.metrics import basic_metric
from rocketsonde.core.summarize import basic_summarizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", help="Path to a log file to write outputs to")
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    monitor = Probe(basic_metric)
    monitor.start_monitor()

    parent = psutil.Process()

    root_child = subprocess.Popen(args.cmd)

    exit_code = root_child.poll()
    while exit_code is None:
        for child in parent.children(recursive=True):
            if monitor.probe_pid() == child.pid:
                continue
            # This is safe to do over and over because adding a pid twice is
            # a relatively cheap NOP
            monitor.attach_to_process(child.pid, " ".join(child.cmdline()))
        sleep(0.25)
        exit_code = root_child.poll()

    monitor.stop_monitor()

    observations = monitor.records
    summaries = basic_summarizer(observations)
    try:
        if args.log:
            out = open(args.log, "a")
        else:
            out = sys.stderr

        for pid, summary in summaries.items():
            key = monitor.user_data(pid)
            formated_output = json.dumps({"pid": pid, "key": key, "summary": summary}, sort_keys=True, indent=4)
            out.write(formated_output + "\n")
    finally:
        if args.log:
            out.close()

    if exit_code is not None:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
