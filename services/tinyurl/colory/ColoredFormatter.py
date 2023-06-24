import logging
# Define a custom formatter class


class ColoredFormatter(logging.Formatter):

    # Define color codes
    GREEN = "\033[1;32m"
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    RESET = "\033[0m"

    def format(self, record):
        # Set the appropriate color based on the log level
        if record.levelno == logging.ERROR:
            color_code = self.RED
        elif record.levelno == logging.INFO:
            color_code = self.GREEN
        else:
            color_code = self.YELLOW

        # Add color codes to the log message
        record.msg = f"{color_code}{record.msg}{self.RESET}"
        return super().format(record)
