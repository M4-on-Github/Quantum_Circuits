# Verifier runtimes and memory

| Verifier | Kaggle CPU kernel (4 workers via fork) | Local Windows 11, i9-14900HX, 32 logical CPUs, 31.7 GB (serial) |
|---|---|---|
| invsqrt (200,540,928 shots) | 1,503 s wall; 0.54 GB per process, 0.71 GB summed tree RSS | 9,056 s wall (2.5 h, ~94% of one core); 0.54 GB peak working set; no stdout until it finishes |
| dqi (102,400 shots) | 449 s wall; 9.5 GB peak per-process, 9.6 GB system used | not run |
| dqi with `--salt` (exp-003, 3 runs) | 366–371 s wall; 9.53 GB peak per-process, ≤ 9.95 GB system used | not run |
| dfthcsos | 137 s wall; 1.2 GB | 356 s wall; 1.1 GB |
| dfthcsos, public 15-circuit 430Q build (1,220 addresses, about 280 Toffoli per circuit; exp-006) | 29.5 and 33.5 s wall; 0.73 GB | 42.8 s wall; 0.86 GB (alone, AC power) |
| dqi with `--salt`, public 889Q decoder (454,507 static Toffoli, 505 MB .kmb; exp-005, 3 runs) | 216 s wall each; 4.86 GB peak per process, ≤ 5.8 GB system used | not run |
| invsqrt, 92Q `src/invsqrt` port (200,540,928 shots, default args; exp-008) | 774.9 s wall; 0.70 GB summed tree RSS, 0.97 GB system used | not run (only `--max-x 20000`, 30 s) |
| invsqrt, same 92Q port with `--salt exp-009-S-002` (exp-009) | 973.3 s wall; 0.71 GB summed tree RSS, 0.99 GB system used | not run |

- dqi accounting pipeline on Kaggle (exp-003):
  - Loading the sample `dqi.kmb` takes 3.8 s.
  - `to_file(format='kmx')` takes 14.3 s and writes 1.54 GB (86.1M lines).
  - The streaming `kmx_tag_count` takes 111 s.
  - Peak memory is 3.57 GB per process.
  - Generator build, sample load, `==`, plus the count: 4.47 GB peak.
- Same pipeline on the public 889Q dqi .kmb (exp-005, Kaggle): load 0.6 s, `to_file(format='kmx')` 7.9 s for 762.6 MB (55.8M lines), `kmx_tag_count` 47 s, count step 94 s at 4.83 GB peak. A whole-circuit `sim.do` on 2,048 verifier-distributed shots takes 16.7 s. Four parallel segsim workers of 2,048 shots took 137 s wall and 4.9 GB each, 20.3 GB system used.
- To analyse a large circuit as text off Kaggle, have a kernel write the .kmx and compress it with Python `lzma` (preset 6): 762.6 MB of .kmx became 16.6 MB in 240 s, with 0.53 GB peak RSS (exp-005, kernel `rainm4/exp-005-dqi-kmx-dump`). Locally, streaming that .xz through `lzma.open(..., 'rt')` with a line parser takes about 90 s.
- So run full invsqrt verifies on Kaggle. The dqi CLI's "~6 GB per worker" estimate did not hold: the whole forked tree stayed under 10 GB.
- The local figures come from three verifiers running concurrently.
- A local dfthcsos verify of the sample took 1,017 s wall with a 1.11 GB peak RSS (exp-002). For the first ~11 min it got only about 98 CPU-s, then about 1 CPU-s/s. It was mostly alone, but exp-004's dfthcsos verify overlapped its last ~69 s. The laptop was on battery (`BatteryStatus.Discharging` True); that this caused the slowdown is untested. Two concurrent runs of the same verifier in the exp-002 review took about 330 s each (1.04 GB). Expect 5.5–17 min locally.
- Waiting on a background job: `powershell.exe -NoProfile -Command "Wait-Process -Id <pid> -Timeout 590"` works. If it exceeds the Bash tool's 600 s limit, the call moves itself to the background (exp-002).
- The machine runs at about 92% commit charge with the user's normal apps open (Edge alone about 14 GB private). Check `Win32_OperatingSystem` free memory before starting dqi locally.
