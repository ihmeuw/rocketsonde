import json

from db_tools.ezfuncs import get_connection


def write_summary_to_db(pid, key, summary, database, table="rocketsonde_summary"):
    q = """insert into {table} (pid, key, inserted_at, summary)
           values (%(pid), %(key), now(), %(summary))"""
    summary = json.dumps(summary, sort_keys=True)
    key = json.dumps(key, sort_keys=True)

    connection = get_connection(database)
    try:
        connection.execute(q, args={"pid": pid, "key": key, "summary": summary})
    finally:
        connection.close()


def summary_to_line(pid, key, summary):
    return json.dumps({"pid": pid, "key": key, "summary": summary}, sort_keys=True)


def append_summary_to_file(pid, key, summary, path):
    line = summary_to_line(pid, key, summary)
    with open(path, "a") as f:
        f.write(line)
