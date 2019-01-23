import psutil


def basic_metric(pid):
    try:
        p = psutil.Process(pid)
        rss = p.memory_full_info().rss
        uss = p.memory_full_info().uss
        cpu = p.cpu_times()
        return {"rss": rss, "uss": uss, "user": cpu.user, "system": cpu.system}
    except psutil.NoSuchProcess:
        return None
