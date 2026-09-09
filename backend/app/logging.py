import logging

# Timestamps matter more here than anywhere else: the only record of a scrape run
# is the launchd log, and without them it cannot answer when a run happened or how
# long it took.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cine-uio")
