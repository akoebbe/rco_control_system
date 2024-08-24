import adafruit_logging as logging
import gc
import microcontroller
class MemHandler(logging.StreamHandler):
    def format(self, record: logging.LogRecord):
        mem_pct = (gc.mem_alloc() / (gc.mem_alloc() + gc.mem_free())) * 100
        return f"{record.created:<0.3f} - {mem_pct:4.1f}% - {microcontroller.cpu.temperature:3.1f}C - {record.levelname} - {record.msg}"


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
log_handler = MemHandler()
LOGGER.addHandler(log_handler)
