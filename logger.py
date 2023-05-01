import logging


def setup_logging():
    # set up the logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs.txt', mode='w')
        ]
    )

    # add a filter to the file handler to only log warnings or errors
    file_handler = logging.getLogger().handlers[1]
    file_handler.addFilter(logging.Filter('main'))
    file_handler.setLevel(logging.WARNING)
