import csv
import importlib
import os
import subprocess
import sys

import psutil
import pytest

from ..main import MemoryMetricUnavailable, all_children, get_memory, main, monitor

TEST_CODE = """
import subprocess
p = subprocess.Popen('sleep 5'.split())
p.wait()
"""


class MemoryInfo:
    def __init__(self, rss=0, vms=0, pss=None, uss=None):
        self.rss = rss
        self.vms = vms
        if pss is not None:
            self.pss = pss
        if uss is not None:
            self.uss = uss


class FakeProcess:
    def __init__(self, rss=0, vms=0, pss=None, uss=None):
        self.info = MemoryInfo(rss=rss, vms=vms, pss=pss, uss=uss)
        self.full_info_called = False

    def memory_info(self):
        return self.info

    def memory_full_info(self):
        self.full_info_called = True
        return self.info


def test_get_memory_default_uses_rss():
    process = FakeProcess(rss=10, pss=20, uss=30)
    assert get_memory(process) == 10
    assert not process.full_info_called


def test_get_memory_rss_uses_rss():
    process = FakeProcess(rss=10, pss=20, uss=30)
    assert get_memory(process, "rss") == 10
    assert not process.full_info_called


def test_get_memory_pss_uses_full_info_pss():
    process = FakeProcess(rss=10, pss=20, uss=30)
    assert get_memory(process, "pss") == 20
    assert process.full_info_called


def test_get_memory_uss_uses_full_info_uss():
    process = FakeProcess(rss=10, pss=20, uss=30)
    assert get_memory(process, "uss") == 30
    assert process.full_info_called


def test_get_memory_unavailable_metric_message():
    process = FakeProcess(rss=10)
    with pytest.raises(MemoryMetricUnavailable, match="pss.*not available.*rss"):
        get_memory(process, "pss")


def test_all_children(tmpdir):
    filename = tmpdir.join("test.py").strpath

    with open(filename, "w") as f:
        f.write(TEST_CODE)

    p = subprocess.Popen(f"{sys.executable} {filename}".split())

    import time

    time.sleep(1)

    pr = psutil.Process(p.pid)
    children = all_children(pr)
    assert len(children) > 0
    p.kill()


class TestMonitor:
    def setup_method(self, method):
        self.p = subprocess.Popen("sleep 10", shell=True)

    def teardown_method(self, method):
        self.p.kill()

    def test_simple(self):
        monitor(self.p.pid, duration=3)

    def test_simple_with_interval(self):
        monitor(self.p.pid, duration=3, interval=0.1)

    def test_with_children(self, tmpdir):
        # Test with current process since it has a subprocess (self.p)
        monitor(os.getpid(), duration=3, include_children=True)

    def test_logfile(self, tmpdir):
        filename = tmpdir.join("test_logfile").strpath
        monitor(self.p.pid, logfile=filename, duration=3)
        assert os.path.exists(filename)
        assert len(open(filename).readlines()) > 0

    def test_logfile_csv(self, tmpdir):
        filename = tmpdir.join("test_logfile.csv").strpath
        monitor(self.p.pid, logfile=filename, duration=3, log_format="csv")
        assert os.path.exists(filename)
        assert len(open(filename).readlines()) > 0
        with open(filename) as csvfile:
            data = csv.reader(csvfile)
            assert next(data) == ["elapsed_time", "nproc", "cpu", "mem_real", "mem_virtual"]

    def test_include_children_sums_selected_metric(self, tmpdir, monkeypatch):
        filename = tmpdir.join("test_logfile.csv").strpath

        class Process:
            def __init__(self, pid, rss, vms, pss, children=None):
                self.pid = pid
                self.info = MemoryInfo(rss=rss, vms=vms, pss=pss)
                self._children = children or []
                self.status_calls = 0

            def status(self):
                self.status_calls += 1
                return psutil.STATUS_RUNNING if self.status_calls == 1 else psutil.STATUS_ZOMBIE

            def cpu_percent(self):
                return 0

            def memory_info(self):
                return self.info

            def memory_full_info(self):
                return self.info

            def children(self, recursive=True):
                return self._children

        child = Process(2, rss=100, vms=1024**2, pss=10 * 1024**2)
        parent = Process(1, rss=100, vms=2 * 1024**2, pss=20 * 1024**2, children=[child])
        monkeypatch.setattr(psutil, "Process", lambda pid: parent)
        main_module = importlib.import_module("psrecord.main")
        monkeypatch.setattr(main_module, "children", [])

        monitor(1, logfile=filename, log_format="csv", include_children=True, memory_metric="pss")

        with open(filename) as csvfile:
            rows = list(csv.reader(csvfile))

        assert rows[0] == ["elapsed_time", "nproc", "cpu", "mem_pss", "mem_virtual"]
        assert int(rows[1][1]) == 2
        assert float(rows[1][3]) == 30

    def test_plot(self, tmpdir):
        pytest.importorskip("matplotlib")
        filename = tmpdir.join("test_plot.png").strpath
        monitor(self.p.pid, plot=filename, duration=3)
        assert os.path.exists(filename)

    def test_main(self):
        sys.argv = ["psrecord", "--duration=3", "'sleep 10'"]
        main()

    def test_main_by_id(self):
        sys.argv = ["psrecord", "--duration=3", str(os.getpid())]
        main()

    @pytest.mark.skipif(sys.platform == "darwin", reason="Functionality not supported on MacOS")
    def test_io(self, tmpdir):
        monitor(os.getpid(), duration=3, include_io=True)
