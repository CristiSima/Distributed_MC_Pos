#!/usr/bin/python
from operator import mul as mul_org, itruediv
from functools import reduce
from copy import deepcopy

def mul(*args): return reduce(mul_org, args, 1)

def roundup(nr): return (int(nr) if nr == round(nr) else int(nr)+1)

def proc(target):
    target["speed"]=int(round(target["core_count"]*target["score"]))
    target["speed"]=target["score"]

# proc(cpu)
# proc(gpu)


def single_balance(cpu, gpu):
    if cpu["score"]>gpu["score"]:
        ratio=(cpu["score"]/gpu["score"])
        weight=(1, ratio)
    else:
        ratio=(gpu["score"]/cpu["score"])
        weight=(ratio, 1)

    print(weight)
    # return weight
    total_weight=sum(weight)

    weight=list(map(lambda x:x/total_weight, weight))
    print(weight)

    final_time=list(map(mul, weight, [cpu["score"], gpu["score"]]))

    print()
    print(final_time)

    exit()

    thread_counts=list(map(round, map(mul, weight, [cpu["core_count"], gpu["core_count"]])))

    print(thread_counts)

    return thread_counts


def get_field(targets, field_name):
    return [target[field_name] for target in targets]

def get_core_counts(targets): return get_field(targets, "core_count")
def get_scores(targets): return get_field(targets, "score")

def get_thread_distribution(units, overload_factors):
    return list(map(mul, get_core_counts(units), overload_factors))

def calc_proccessing_times(units, overload_factors):
    '''
    aproximates the system execution time (start -> last finish)

    a batch is a set of up to <cores> threads, the execution time of a batch is independent of the number of threads in it
    '''
    thread_distribution=get_thread_distribution(units, overload_factors)
    thread_count=sum(thread_distribution)

    times=list(map(mul,
        thread_distribution, get_scores(units), [1/thread_count,]*len(overload_factors)
    ))
    # print(times)
    return times

def calc_proccessing_duration(units, overload_factors):
    return max(calc_proccessing_times(units, overload_factors))

def calc_proccessing_delta(units, overload_factors):
    times=calc_proccessing_times(units, overload_factors)
    return max(times)-min(times)

def add_best_batch(units, overload_factors, base_time=None):
    '''
    tries to generate a better(lower system execution time) configuration(distribution of threads/overload_factors)
    '''
    if not base_time:
        base_time=calc_proccessing_duration(units, overload_factors)

    best_time=base_time

    for idx, batch_size in enumerate(get_core_counts(units)):
        next_time=calc_proccessing_duration(units, conf_add(overload_factors, idx, 1))
        if best_time > next_time:
            best_time = next_time
            next_overload_factors=conf_add(overload_factors, idx, 1)

    if base_time>best_time:
        return True, next_overload_factors, best_time

    return False, overload_factors, base_time

def complete_batch(units, overload_factors):
    '''
    a greedy aproach to generate the best (lower system execution time) configuration (distribution of threads/overload_factors)
    '''
    best_time=None

    while True:
        found, overload_factors, best_time=add_best_batch(units, overload_factors, best_time)
        if not found:
            break

    return overload_factors, best_time

def conf_add(conf, target_idx, val):
    return [e if i != target_idx else e+val for i, e in enumerate(conf)]

def test():
    cpu= {
        "core_count": 12,
        "score": 11.093
    }

    gpu= {
        "core_count": 4608,
        "score": 2.04
    }

    units=[cpu, gpu, gpu]
    # conf=[0, 4608, 4608]
    overload_factors=[0, 1, 1]

    units=[cpu, cpu, gpu]
    # conf=[0, 0, 4608]
    overload_factors=[0, 0, 1]
    # conf=[0, 4608, 0]
    overload_factors=[0, 1, 0]


    units=[cpu, gpu]
    # conf=[0, 4608]
    overload_factors=[0, 1]

    print("cpu", cpu)
    print("gpu", gpu)

    base_time=calc_proccessing_duration(units, overload_factors)

    print(base_time)
    print(*add_best_batch(units, overload_factors))


    print(*complete_batch(units, overload_factors))
    print(calc_proccessing_delta(units, complete_batch(units, overload_factors)[0]))


if __name__ == "__main__":
    test()


'''

Dt=....

Dt*speed*batches ~=T

speed_thread= dt * W_thread

speed_system= speed_thread * nr_threads


BENCHMARK:
    t = speed_thread * nr_threads * ( W / core_count )
      = speed_thread * W

    speed_thread    nr_threads      WORK
S1:     s1             n1           W1
S2:     s2             n2           W2

W1+W2=W

k= s/n

d1= s1 *W1 / n1
d2= s2 *W2 / n2

s1 *W1 / n1 = s2 *W2 / n2
W1/W2 = s2/s1 * n1/n2

W1/W2 = k2/k1

    speed_thread    nr_threads      WORK
S1:     10             100           W1
S2:     20              5            W2


k1= 0.1
k2= 4

W1 = 40 W2

Wn = W * (threads_n / thread_count)


pp nr_threads
    v0= map (*nr_threads) weight
    v0= round(v0)

    v1 = trim_down_to_batch_multiple v0

    while E unalocated threads
        find unit la care adaugand un batch -> min_global e minim
            add batch

func distribute(weight, nr_threads)
    -> nr_batch, timp_min_global, free_spots_in_batch

    if free_spots_in_batch !=0
        nr_threads+=free_spots_in_batch
        => reducere timp_min_global cu ~ nr_threads/(nr_threads+free_spots_in_batch)

func fill_best_batch(batches, current_time=None)
    -> can_be_optimized, new_batches, new_distribution_time
    given a batch config, tries to add 1 batch to minimize time

func repeated_fill_best_batch(batches, current_time=None)
    -> new_batches, new_distribution_time
    calls fill_best_batch until there is no batch


1 -> 2      1->1/2     x2
2 -> 3      1/2->1/3   x3/2

nr_threads ideal: cmmmc(c)


goal:
    timp total MINIM

cum:
    utilizare cat mai mare a tuturor unitatilor(CPU/GPU) de procesare
        utilizare cat mai mare a fiecareui thread

DAR
    tipul unei unitati ~= nr de batch-uri
        => echilibrare la nivel de batch-uri
           prioritate la unitatile mai rapide


SIMPLITATE > PERFECT
    poate sa crape orice, nui bai


PLAN
    implement repeated_fill_best_batch
    extend to multiple units

'''
