from prometheus_client import Counter, Gauge, start_http_server

# Metrics definitions
COMMITS_TOTAL = Counter("sbsync_commits_total", "Total number of git commits")
PUSHES_TOTAL = Counter("sbsync_pushes_total", "Total number of git pushes")
ERRORS_TOTAL = Counter("sbsync_errors_total", "Total number of errors encountered")
LAST_SYNC_TIMESTAMP = Gauge(
    "sbsync_last_sync_timestamp", "Timestamp of the last successful sync"
)
FILES_CHANGED_TOTAL = Counter(
    "sbsync_files_changed_total", "Total number of file change events detected"
)


def start_metrics_server(port):
    start_http_server(port)
