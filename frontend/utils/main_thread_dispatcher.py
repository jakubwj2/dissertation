import logging
import queue
from typing import Optional

logger = logging.getLogger(__name__)


class MainThreadDispatcher:
    def __init__(self, max_tasks_per_poll: Optional[int] = None):
        self.queue = queue.Queue()
        self.max_tasks_per_poll = max_tasks_per_poll

    def queue_task(self, task):
        self.queue.put(task)

    def poll(self):
        processed = 0

        while True:
            if (
                self.max_tasks_per_poll is not None
                and processed >= self.max_tasks_per_poll
            ):
                break

            try:
                task = self.queue.get_nowait()
            except queue.Empty:
                break

            task()

            processed += 1
