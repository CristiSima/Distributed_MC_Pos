#include<stdio.h>
#include<stdlib.h>


#define MODE 1


#include "base.h"

#if !defined(NUM_BLOCKS)
    #define NUM_BLOCKS 6
#endif

#if !defined(NUM_THREADS)
    #define NUM_THREADS 768
#endif

#if !defined(THREAD_OVERLOAD)
    #define THREAD_OVERLOAD 1
#endif

#if !defined(WORKER_OFFSET)
    #define WORKER_OFFSET 0
#endif

#if !defined(TOTAL_WORKERS)
    #define TOTAL_WORKERS (NUM_THREADS*NUM_BLOCKS)
#endif

__global__ void print_from_gpu(void) {
    int sum=0;
    int y=10;
    int dx=threadIdx.x*WORLD_LIMIT;
    for(int x=0;x<WORLD_LIMIT;x++) for(int z=0;z<WORLD_LIMIT;z++)
    {
        if(check_pos(x+dx, y, z))
        {
            printf("FOUND @ %d %d %d\n", x+dx, y, z);
            sum++;
        }
    }
    if(sum!=0)
	printf("Hello World! from thread [%d,%d]  %d\n", threadIdx.x, blockIdx.x, sum);
}


__global__ void cool_search_wraper()
{
    for(int id_overload=0;id_overload<THREAD_OVERLOAD;id_overload++)
        cool_search(WORKER_OFFSET, TOTAL_WORKERS, threadIdx.x+blockIdx.x*blockDim.x+ id_overload*(blockDim.x*gridDim.x));
}



int main(void) {
	printf("GPU[%3d, %3d] with limit %8d\n", NUM_BLOCKS, NUM_THREADS, WORLD_LIMIT);
    fflush(stdout);

    #define cool_search_standalone(workers) cool_search_wraper<<<1,workers>>>(0, workers);
    #define cool_search_test(offset, total_workers) cool_search_wraper<<<1,1>>>(offset, total_workers);
    cool_search_wraper<<<NUM_BLOCKS, NUM_THREADS>>>();

    cudaError_t cuda_error=cudaGetLastError();
    if(cuda_error!=cudaSuccess)
        printf("%s\n%s\n", cudaGetErrorName(cuda_error), cudaGetErrorString(cuda_error));
    // cool_search_standalone(768);
    // cool_search_standalone(768);
    // cool_search_standalone(1);
    // cool_search_test(1, 2);
    // cool_search_wraper<<<1,768>>>(0, 768);
	// print_from_gpu<<<1,768>>>();
	// print_from_gpu<<<1,768>>>();
	// print_from_gpu<<<1,400>>>();
	cudaDeviceSynchronize();
    printf("GPU DONE\n");
    return 0;
}

// nvcc main.cu      -o main; $runTime = (Measure-Command { .\main.exe | Out-Default }).TotalSeconds; Write-Host "GPU RunTime:  " $runTime s
// g++  main.cpp -O2 -o main; $runTime = (Measure-Command { .\main.exe | Out-Default }).TotalSeconds; Write-Host "CPU RunTime:  " $runTime s
