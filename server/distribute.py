#!/usr/bin/python
from operator import mul as mul_org, itruediv
from functools import reduce
from copy import deepcopy

def mul(*args): return reduce(mul_org, args, 1)

def roundup(nr): return (int(nr) if nr == round(nr) else int(nr)+1)

def proc(target):
    target["speed"]=int(round(target["cores"]*target["score"]))
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

    cores=list(map(round, map(mul, weight, [cpu["cores"], gpu["cores"]])))

    print(cores)

    return cores


def get_field(targets, field_name):
    return [target[field_name] for target in targets]

def get_cores(targets): return get_field(targets, "cores")
def get_scores(targets): return get_field(targets, "score")



def calc_proccessing_times(units, threads):
    '''
    aproximates the system execution time (start -> last finish)

    a batch is a set of up to <cores> threads, the execution time of a batch is independent of the number of threads in it
    '''
    total_threads=sum(threads)

    batches=list(map(roundup,
        map(itruediv,
            threads, get_cores(units)
        )
    ))
    # print(batches)
    times=list(map(mul,
        batches, get_scores(units), get_cores(units), [1/total_threads,]*len(batches)
    ))
    # print(times)
    return times

def calc_proccessing_duration(units, threads):
    return max(calc_proccessing_times(units, threads))

def calc_proccessing_delta(units, threads):
    times=calc_proccessing_times(units, threads)
    return max(times)-min(times)

def add_best_batch(threads, units, base_time=None):
    '''
    tries to generate a better(lower system execution time) configuration(distribution of threads)
    '''
    if not base_time:
        base_time=calc_proccessing_duration(units, threads)

    best_time=base_time

    for idx, batch_size in enumerate(get_cores(units)):
        next_time=calc_proccessing_duration(units, conf_add(threads, idx, batch_size))
        if best_time > next_time:
            best_time = next_time
            next_threads=conf_add(threads, idx, batch_size)

    if base_time!=best_time:
        return True, next_threads, best_time

    return False, threads, best_time

def complete_batch(conf, units):
    '''
    a greedy aproach to generate the best (lower system execution time) configuration (distribution of threads)
    '''
    best_time=None

    while True:
        found, conf, best_time=add_best_batch(conf, units, best_time)
        if not found:
            break

    return conf, best_time

def conf_add(conf, target_idx, val):
    return [e if i != target_idx else e+val for i, e in enumerate(conf)]

def test():
    cpu= {
        "cores": 12,
        "score": 11.093
    }

    gpu= {
        "cores": 4608,
        "score": 2.04
    }

    units=[cpu, gpu, gpu]
    conf=[0, 4608, 4608]

    units=[cpu, cpu, gpu]
    conf=[0, 0, 4608]
    # conf=[0, 4608, 0]

    units=[cpu, gpu]
    conf=[0, 4608]

    print("cpu", cpu)
    print("gpu", gpu)

    base_time=calc_proccessing_duration(units, conf)

    print(base_time)
    print(*add_best_batch(conf, units))



    print(*complete_batch(conf, units))
    print(calc_proccessing_delta(units, complete_batch(conf, units)[0]))


if __name__ == "__main__":
    test()


'''

Dt=....

Dt*speed*batches ~=T

speed_thread= dt * W_thread

speed_system= speed_thread * nr_threads


BENCHMARK:
    t = speed_thread * nr_threads * ( W / cores )
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

Wn = W * (threads_n / total_threads)


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
