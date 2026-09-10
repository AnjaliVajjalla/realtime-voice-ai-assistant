import time
from contextlib import contextmanager


@contextmanager
def time_stage(label: str, results: dict):
    """Time a block of code and store the elapsed seconds in results[label].

    Usage:
        results = {}
        with time_stage("transcribe", results):
            transcript = transcribe(audio)
        print(results["transcribe"])  # elapsed seconds
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        results[label] = round(elapsed, 3)
