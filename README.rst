|Coverage Status|

About
=====

``psrecord`` is a small utility that uses the
`psutil <https://github.com/giampaolo/psutil/>`__ library to record the CPU
and memory activity of a process. The package is still under development
and is therefore experimental.

The code is released under a Simplified BSD License, which is given in
the ``LICENSE`` file.

Requirements
============

-  Python 2.7 or 3.3 and higher
-  `psutil <https://code.google.com/p/psutil/>`__ 1.0 or later
-  `matplotlib <http://www.matplotlib.org>`__ (optional, used for
   plotting)

Installation
============

To install, simply do::

    pip install psrecord

To install with the optional plotting dependencies, do::

    pip install psrecord[plot]

Usage
=====

Basics
------

To record the CPU and memory activity of an existing process to a file (use sudo for a root process):

::

    psrecord 1330 --log activity.txt

where ``1330`` is an example of a process ID which you can find with
``ps`` or ``top``. You can also use ``psrecord`` to start up a process
by specifying the command in quotes:

::

    psrecord "hyperion model.rtin model.rtout" --log activity.txt

Plotting
--------

To make a plot of the activity:

::

    psrecord 1330 --plot plot.png

This will produce a plot such as:

.. image:: https://github.com/astrofrog/psrecord/blob/main/screenshot.png

You can combine these options to write the activity to a file and make a
plot at the same time:

::

    psrecord 1330 --log activity.txt --plot plot.png

Duration and intervals
----------------------

By default, the monitoring will continue until the process is stopped.
You can also specify a maximum duration in seconds:

::

    psrecord 1330 --log activity.txt --duration 10

Finally, the process is polled as often as possible by default, but it
is possible to set the time between samples in seconds:

::

    psrecord 1330 --log activity.txt --interval 2

Subprocesses
------------

To include sub-processes in the CPU and memory stats, use:

::

    psrecord 1330 --log activity.txt --include-children

You can choose which memory metric is recorded and plotted with
``--memory-metric``. The default, ``rss``, matches the original psrecord
behavior. ``pss`` and ``uss`` use ``psutil.memory_full_info()`` and are
mainly available on Linux. For example::

    psrecord "python script.py" --include-children --interval 1 --memory-metric pss --log usage.txt --plot usage.png

RSS is the resident memory each process sees, so shared memory can be
over-counted when summing multiple processes. PSS distributes shared pages
proportionally and is often a better estimate for multi-process workloads on
Linux. USS counts fully private memory, which is more conservative and is
usually lower than the total memory used by a job.

Running tests
=============

To run tests, you will need `pytest <https://docs.pytest.org/en/latest/>`_. You can install it with::

    pip install pytest
    
You can then run the tests with::

    pytest psrecord

Reporting issues
================

Please report any issues in the `issue
tracker <https://github.com/astrofrog/psrecord/issues>`__.

.. |Coverage Status| image:: https://codecov.io/gh/astrofrog/psrecord/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/astrofrog/psrecord
