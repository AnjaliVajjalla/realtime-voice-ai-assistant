import time
from src.trace import time_stage


def test_time_stage_records_positive_elapsed_time():
    results = {}
    with time_stage("test_step", results):
        time.sleep(0.01)  # 10ms, so elapsed should be measurably > 0

    assert "test_step" in results
    assert results["test_step"] > 0


def test_time_stage_still_records_time_if_the_block_raises():
    results = {}
    try:
        with time_stage("failing_step", results):
            raise ValueError("boom")
    except ValueError:
        pass

    # even though the block raised, we should still have timed it
    assert "failing_step" in results
    assert results["failing_step"] >= 0
