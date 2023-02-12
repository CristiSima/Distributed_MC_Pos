#include<stdio.h>
#include<stdlib.h>
#include <pthread.h>


#define MODE 2

#include "base.h"

#if !defined(CORE_COUNT)
    #define CORE_COUNT 12
#endif

#if !defined(OVERLOAD_FACTOR)
    #define OVERLOAD_FACTOR 1
#endif

#if !defined(LOCAL_OFFSET)
    #define LOCAL_OFFSET 0
#endif

#if !defined(THREAD_COUNT)
    #define THREAD_COUNT CORE_COUNT
#endif

typedef struct {
    int worker_offset;
    int total_workers;
    int worker_id;
} worker_info;

void *search_overloader(void *worker_id)
{
    for(int id_overload=0;id_overload<OVERLOAD_FACTOR;id_overload++)
        search_function(LOCAL_OFFSET, THREAD_COUNT, ((int)(llong)worker_id) + id_overload*CORE_COUNT);

    return NULL;
}


int main(void) {
    printf("CPU[%3d]     with limit %8d\n", CORE_COUNT, WORLD_LIMIT);


    pthread_t threads[CORE_COUNT];
    worker_info args[CORE_COUNT];

    for (int id = 0; id < CORE_COUNT; id++) {
            // args[id].worker_offset=0;
            // args[id].total_workers=CORE_COUNT;
            // args[id].worker_id=id;

            pthread_create(&threads[id], NULL, (void* (*)(void*))search_overloader, (void *)(llong)id);
    }
    // cool_search(0, 1, 0);
    for (int id = 0; id < CORE_COUNT; id++)
        pthread_join(threads[id], NULL);
return 0;
}

// nvcc main.cu -o main; $runTime = (Measure-Command { .\main.exe | Out-Default }).TotalSeconds; Write-Host "RunTime:  " $runTime s
// g++  main.cpp -o main; $runTime = (Measure-Command { .\main.exe | Out-Default }).TotalSeconds; Write-Host "RunTime:  " $runTime s
