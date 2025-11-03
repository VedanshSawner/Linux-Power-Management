#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int write_to_file(const char *path, const char *value) {
    FILE *fp = fopen(path, "w");
    if (fp == NULL) { return -1; } // Ignore errors if a CPU core file doesn't exist
    fprintf(fp, "%s", value);
    fclose(fp);
    return 0;
}

int read_from_file(const char *path, char *buffer, size_t len) {
    FILE *fp = fopen(path, "r");
    if (fp == NULL) { return -1; }
    if (fgets(buffer, len, fp) == NULL) { return -1; }
    fclose(fp);
    buffer[strcspn(buffer, "\n")] = 0; // Remove trailing newline
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <get | set <governor>>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "get") == 0) {
        char buffer[64];
        if (read_from_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", buffer, sizeof(buffer)) == 0) {
            printf("%s\n", buffer);
        } else {
            fprintf(stderr, "Error reading current governor.\n");
            return 1;
        }
    } else if (strcmp(argv[1], "set") == 0) {
        if (argc != 3) {
            fprintf(stderr, "Usage: %s set <governor_name>\n", argv[0]);
            return 1;
        }
        char *governor = argv[2];
        char path[256];
        int updated_cores = 0;
        // Loop through a reasonable number of cores
        for (int i = 0; i < 64; i++) {
            snprintf(path, sizeof(path), "/sys/devices/system/cpu/cpu%d/cpufreq/scaling_governor", i);
            if (write_to_file(path, governor) == 0) {
                updated_cores++;
            }
        }
        printf("Set governor to '%s' for %d cores.\n", governor, updated_cores);
    } else {
        fprintf(stderr, "Invalid command.\n");
        return 1;
    }
    return 0;
}