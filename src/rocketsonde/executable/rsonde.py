import json
import argparse
import sys
import subprocess

from rocketsonde.core.probe import Probe
from rocketsonde.core.metrics import basic_metric
from rocketsonde.core.summarize import basic_summarizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    monitor = Probe(basic_metric)
    monitor.start_monitor()

    process = subprocess.Popen(args.cmd)
    monitor.attach_to_process(process.pid)
    process.wait()

    observations = monitor.records
    summaries = basic_summarizer(observations)
    for pid, summary in summaries.items():
        key = {}
        formated_output = json.dumps({"pid": pid, "key": key, "summary": summary}, sort_keys=True, indent=4)
        sys.stderr.write(formated_output)


if __name__ == "__main__":
    main()
