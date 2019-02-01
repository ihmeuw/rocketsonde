def _measurement_period(observations):
    if len(observations) == 0:
        raise ValueError("Can't interpret an empty observation set")
    start = observations[0]["time"]
    end = observations[0]["time"]
    for record in observations:
        time = record["time"]
        if time < start:
            start = time
        if time > end:
            end = time
    return start, end


def basic_summarizer(records):
    results = {}
    for process_key, process_observations in records.items():
        keys = set(process_observations[0].keys())
        assert all([set(o.keys()) == keys for o in process_observations])
        keys -= {"time"}
        first_time, last_time = _measurement_period(process_observations)

        sums = {k: 0 for k in keys}
        peaks = {k: process_observations[0][k] for k in keys}
        for observation in process_observations:
            for k in keys:
                sums[k] += observation[k]
                if peaks[k] < observation[k]:
                    peaks[k] = observation[k]
        result = {f"mean_{k}": v / len(process_observations) for k, v in sums.items()}
        result.update({f"peak_{k}": v for k, v in peaks.items()})

        result["total_samples"] = len(process_observations)
        result["start_time"] = first_time
        result["end_time"] = last_time

        results[process_key] = result
    return results
