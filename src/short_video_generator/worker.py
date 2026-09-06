import logging


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info(
        "Worker boundary is ready; job claiming and pipeline execution are deferred."
    )


if __name__ == "__main__":
    run()

