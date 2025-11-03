#include <stdio.h>
#include <string.h>
#include <unistd.h> // For access()

// Find the first available AC adapter and read its 'online' status
int main() {
    char path[256];
    char *common_paths[] = {
        "/sys/class/power_supply/AC/online",
        "/sys/class/power_supply/AC0/online",
        "/sys/class/power_supply/ACAD/online",
        "/sys/class/power_supply/ADP1/online",
        NULL
    };

    FILE *fp = NULL;
    for (int i = 0; common_paths[i] != NULL; i++) {
        if (access(common_paths[i], R_OK) == 0) {
            fp = fopen(common_paths[i], "r");
            break;
        }
    }

    if (fp == NULL) {
        fprintf(stderr, "Error: Could not find AC power supply.\n");
        return 1;
    }

    int status = 0;
    fscanf(fp, "%d", &status);
    fclose(fp);

    if (status == 1) {
        printf("online\n");
    } else {
        printf("offline\n");
    }
    return 0;
}