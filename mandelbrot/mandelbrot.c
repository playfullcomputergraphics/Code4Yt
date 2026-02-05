#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
//
//gcc -O3 -march=native -o mandelbrot mandelbrot.c -lm
//
static inline double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(void) {
    const int width  = 1000;
    const int height = 1000;
    const int maxIter = 512;

    const double x_min = -2.0;
    const double x_max =  1.0;
    const double y_min = -1.5;
    const double y_max =  1.5;

    unsigned long long checksum = 0ULL;

    double t0 = now_sec();

    for (int j = 0; j < height; ++j) {
        double cy = y_min + (y_max - y_min) * (double)j / (double)(height - 1);

        for (int i = 0; i < width; ++i) {
            double cx = x_min + (x_max - x_min) * (double)i / (double)(width - 1);

            int iter = 0;

            /* --- Cardioid / Period-2 bulb test --- */
            double x = cx;
            double y = cy;

            /* Period-2 bulb */
            double q = (x + 1.0)*(x + 1.0) + y*y;
            if (q < 0.0625) {
                iter = maxIter;
            } else {
                /* Main cardioid */
                double p = sqrt((x - 0.25)*(x - 0.25) + y*y);
                if (x < p - 2.0*p*p + 0.25) {
                    iter = maxIter;
                } else {
                    /* Escape-time iteration */
                    double zx = 0.0;
                    double zy = 0.0;

                    while (zx*zx + zy*zy <= 4.0 && iter < maxIter) {
                        double zx_new = zx*zx - zy*zy + cx;
                        zy = 2.0 * zx * zy + cy;
                        zx = zx_new;
                        ++iter;
                    }
                }
            }

            checksum += iter;
        }
    }

    double t1 = now_sec();

    printf("Compute time: %.6f s\n", t1 - t0);
    printf("Checksum: %llu\n", checksum);

    return 0;
}
