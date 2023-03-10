typedef long long llong;


#if !defined(MODE)
    #error MODE NOT SPECIFIED
#endif

#define CUDA_CODE 1
#define GCC_CODE  2

#if MODE == CUDA_CODE
    #define MODIFIER __device__
    #define CHECK_NO_INLINE

#elif MODE == GCC_CODE
    #define MODIFIER
    #define CHECK_NO_INLINE __attribute__ ((noinline))
#else
    #error UNKNOWN MODE
#endif



MODIFIER int getQuads_inline(int x, int y, int z)
{
    llong seed = (llong)(x * 3129871) ^ (llong)z * 116129781L ^ (llong)y;
    seed = seed * seed * 42317861L + seed * 11L;
    seed= seed >> 16;

    // set seed
    seed=(seed ^ 25214903917L) & 281474976710655L;


    // next_res res1, res2;
    int temp;
    llong res=0;
    // res1 = next(32, seed);
    seed = (seed * 25214903917L + 11L) & 281474976710655L;
    temp=seed >> 48 - 32;
    res=((llong)temp)<<32;
    // return {res=res, seed=seed};

    // res2 = next(32, res1.seed);
    seed = (seed * 25214903917L + 11L) & 281474976710655L;
    temp=seed >> 48 - 32;
    res|=temp;


    // llong res=  (llong)res1.res << 32;
    // res+=       (llong)res2.res;

    return abs((int)res) % 4;
}


#define height 20

MODIFIER int check_pos(int x, int y, int z)
{

    for(int j=0;j<height;j++)
        if(0!=getQuads_inline(x, y+j, z))
            return 0;
    return 1;
}
#if !defined(SQUARE_CHECK_LENGTH)
    #define SQUARE_CHECK_LENGTH 4
#endif
MODIFIER int CHECK_NO_INLINE check_square(int x, int y, int z)
{

    for(int i=0;i<SQUARE_CHECK_LENGTH;i++) for(int j=0;j<SQUARE_CHECK_LENGTH;j++)
        if(0!=getQuads_inline(x+i, y, z+j))
            return 0;

    return 1;
}

#define rect_length 5
#define rect_width 4

MODIFIER int check_rect(int x, int y, int z)
{

    for(int i=0;i<rect_length;i++) for(int j=0;j<rect_width;j++)
        if(0!=getQuads_inline(x+i, y, z+j))
            return 0;

    return 1;
}

MODIFIER int check_custom(int x, int y, int z);

#if !defined(WORLD_LIMIT)
    // #define WORLD_LIMIT (30*1000*1000)
    // #define WORLD_LIMIT (30*1000*10)
    #define WORLD_LIMIT (30*1000*2)
    // #define WORLD_LIMIT (30*1000)
    // #define WORLD_LIMIT (6)
#endif


#if !defined(check_func)
    #define check_func check_square
#endif

#if !defined(MIN_Y)
    #define MIN_Y -61
#endif
#if !defined(MAX_Y)
    #define MAX_Y -61
#endif

MODIFIER void cool_search(int worker_offset, int total_workers, int workerId) {
    int sum=0;
    int y=-61;

    if(workerId>=total_workers)
        return;

    // for(int x=threadIdx.x+1+worker_offset;x<WORLD_LIMIT;x+=total_workers)
    //     for(int offset=1;offset<x;offset++)
    //     {
    //         printf("%d %d %d\n", x-offset, y, offset);
    //         // return;
    //         if(check_pos(x-offset, y, offset))
    //         {
    //             printf("FOUND @ %d %d %d\n", x-offset, y, offset);
    //             sum++;
    //         }
    //     }

    for (int k = workerId+1+worker_offset; k < WORLD_LIMIT ; k+=total_workers) {
        for (int x = 1; x < k ; x++) {
            int z = k - x;
            // printf("%d %d\n", x, z);
            if(check_func(x, y, z))
            {
                printf("FOUND @ %d %d %d\n", x, y, z);
                sum++;
            }
            if(check_func(-x, y, z))
            {
                printf("FOUND @ %d %d %d\n", -x, y, z);
                sum++;
            }
            if(check_func(-x, y, -z))
            {
                printf("FOUND @ %d %d %d\n", -x, y, -z);
                sum++;
            }
            if(check_func(x, y, -z))
            {
                printf("FOUND @ %d %d %d\n", x, y, -z);
                sum++;
            }
        }
    }

    for (int k = WORLD_LIMIT+workerId+worker_offset; k < WORLD_LIMIT+WORLD_LIMIT-1 ; k+=total_workers) {
        for (int x = k - WORLD_LIMIT + 1; x < WORLD_LIMIT; x++) {
            int z = k - x;
            // printf("%d %d\n", x, z);
            if(check_func(x, y, z))
            {
                printf("FOUND @ %d %d %d\n", x, y, z);
                sum++;
            }
            if(check_func(-x, y, z))
            {
                printf("FOUND @ %d %d %d\n", -x, y, z);
                sum++;
            }
            if(check_func(-x, y, -z))
            {
                printf("FOUND @ %d %d %d\n", -x, y, -z);
                sum++;
            }
            if(check_func(x, y, -z))
            {
                printf("FOUND @ %d %d %d\n", x, y, -z);
                sum++;
            }
        }
    }


    if(sum!=0)
	    printf("Thread %3d found: %d\n", workerId, sum);
}

MODIFIER void basic_search(int worker_offset, int total_workers, int workerId) {
    int sum=0;

    for (int x = workerId+1+worker_offset; x < WORLD_LIMIT ; x+=total_workers)
    for (int z = 1; z < WORLD_LIMIT ; z++)
        for(int y=MIN_Y; y<=MAX_Y;y++)
        {
            if(check_func(x, y, z))
            {
                printf("FOUND @ %d %d %d\n", x, y, z);
                sum++;
            }
            if(check_func(-x, y, z))
            {
                printf("FOUND @ %d %d %d\n", -x, y, z);
                sum++;
            }
            if(check_func(-x, y, -z))
            {
                printf("FOUND @ %d %d %d\n", -x, y, -z);
                sum++;
            }
            if(check_func(x, y, -z))
            {
                printf("FOUND @ %d %d %d\n", x, y, -z);
                sum++;
            }
        }


    if(sum!=0)
	    printf("Thread %3d found: %d\n", workerId, sum);
}

#if !defined(search_function)
    #define search_function basic_search
#endif

#include "custom.h"
