from prometheus_client import Counter, Gauge, start_http_server
from src.utils import logger

# Metrics
PULLS_TOTAL = Counter("sbsync_client_pulls_total", "Total number of git pulls")
ERRORS_TOTAL = Counter("sbsync_client_errors_total", "Total number of errors")
LAST_PULL_TIMESTAMP = Gauge(
    "sbsync_client_last_pull_timestamp", "Unix timestamp of last successful pull"
)


def start_metrics_server(port):
    try:
        start_http_server(port)
        logger.info("Metrics server started on port %s", port)
    except Exception as e:
        logger.error("Failed to start metrics server: %s", e)
