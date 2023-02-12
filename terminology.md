(compute_)unit:
- abstraction over cpu/gpu
- core_count
- score: time for benchmark

core:
- fizical core on the compute unit

thread:
- doesn't refer to the classic *thread* managed by the OS.
 - each core will get 1 classic *thread* and on that multiple threads will be ran consecutively
- each thread has an equal share of the workload

overload_factor:
- how many threads will be run on the same core
- per unit value

run_parametrs:
- units
- overload_factors


thread_count:
- total number of threads across all units

local_threads:
- threads started on 1 unit

local_offset:
- offset used for the threads of a unit
