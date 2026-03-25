import time


class Timer:
    def __init__(self, start_immediately: bool = False):
        self.timer = time.time()
        self.total_time = 0
        self.paused = not start_immediately

    def start_timer(self) -> None:
        self.timer = time.time()
        self.total_time = 0
        self.paused = False

    def get_time(self) -> float:
        if self.paused:
            return self.total_time

        return self.total_time + time.time() - self.timer

    def pause_timer(self) -> None:
        self.total_time += time.time() - self.timer
        self.paused = True

    def resume_timer(self) -> None:
        self.timer = time.time()
        self.paused = False

    def stop_timer(self) -> None:
        self.total_time = self.get_time()
        self.paused = True

    def is_paused(self) -> bool:
        return self.paused
