#include<stdio.h>
#include<stdlib.h>
#include <pthread.h>


#define MODE 2

#include "base.h"

#if !defined(NUM_THREADS)
    #define NUM_THREADS 12
#endif

#if !defined(WORKER_OFFSET)
    #define WORKER_OFFSET 0
#endif

#if !defined(TOTAL_WORKERS)
    #define TOTAL_WORKERS NUM_THREADS
#endif

typedef struct {
    int worker_offset;
    int total_workers;
    int worker_id;
} worker_info;

void *cool_search_wraper(void *worker_id)
{
    cool_search(WORKER_OFFSET, TOTAL_WORKERS, (int)(llong)worker_id);

    return NULL;
}


int main(void) {
    printf("CPU[%3d]     with limit %8d\n", NUM_THREADS, WORLD_LIMIT);


    pthread_t threads[NUM_THREADS];
    worker_info args[NUM_THREADS];

    for (int id = 0; id < NUM_THREADS; id++) {
            // args[id].worker_offset=0;
            // args[id].total_workers=NUM_THREADS;
            // args[id].worker_id=id;

            pthread_create(&threads[id], NULL, (void* (*)(void*))cool_search_wraper, (void *)(llong)id);
    }
    // cool_search(0, 1, 0);
    for (int id = 0; id < NUM_THREADS; id++)
        pthread_join(threads[id], NULL);
return 0;
}

// nvcc main.cu -o main; $runTime = (Measure-Command { .\main.exe | Out-Default }).TotalSeconds; Write-Host "RunTime:  " $runTime s
// g++  main.cpp -o main; $runTime = (Measure-Command { .\main.exe | Out-Default }).TotalSeconds; Write-Host "RunTime:  " $runTime s
