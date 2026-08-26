# Benchmarks for the data-model decision (issue #2)

Measurement scripts behind every number in `spec/data-model.md`. Throwaway
code: once #2 decides, this directory has served its purpose.

Run order:

```bash
python3 bench_size_time.py      # file sizes, load+derive timings
python3 bench_gitdiff.py        # git diff after appending one transaction
python3 bench_interrupt.py      # SIGKILL mid-write, both formats
python3 bench_decimal.py        # float vs Decimal on one position history
python3 bench_decimal_mech.py   # where float actually bites
python3 bench_fifo.py           # FIFO vs weighted average worked example
```

Outputs land in `out/` next to these scripts. If your environment restricts
SQLite writes inside the repo tree, redirect with `BENCH_OUT=/some/dir`.

Requires Python 3.10+; no third-party packages.
