import logging


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info(
        "Scheduler boundary is ready; periodic run creation is deferred."
    )


if __name__ == "__main__":
    run()
