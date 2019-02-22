import psutil


def basic_metric(pid):
    try:
        p = psutil.Process(pid)
        rss = p.memory_info().rss
        shared = p.memory_info().shared
        cpu = p.cpu_times()
        return {"rss": rss, "shared": shared, "user": cpu.user, "system": cpu.system}
    except psutil.NoSuchProcess:
        return None
