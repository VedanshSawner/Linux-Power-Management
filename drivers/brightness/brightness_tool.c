#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>

#define BACKLIGHT_PATH "/sys/class/backlight/"

// Helper function to find the first available backlight device name
int find_backlight_device(char *device_name, size_t len) {
    DIR *d = opendir(BACKLIGHT_PATH);
    if (d == NULL) {
        perror("Failed to open " BACKLIGHT_PATH);
        return -1;
    }
    struct dirent *dir;
    int found = 0;
    while ((dir = readdir(d)) != NULL) {
        if (strcmp(dir->d_name, ".") != 0 && strcmp(dir->d_name, "..") != 0) {
            strncpy(device_name, dir->d_name, len - 1);
            device_name[len - 1] = '\0';
            found = 1;
            break;
        }
    }
    closedir(d);
    if (!found) {
        fprintf(stderr, "Error: No backlight device found in %s\n", BACKLIGHT_PATH);
        return -1;
    }
    return 0;
}

// Helper function to read an integer from a file
int read_int_from_file(const char *path) {
    FILE *fp = fopen(path, "r");
    if (fp == NULL) { return -1; }
    int value = 0;
    fscanf(fp, "%d", &value);
    fclose(fp);
    return value;
}

// Helper function to write an integer to a file
int write_int_to_file(const char *path, int value) {
    FILE *fp = fopen(path, "w");
    if (fp == NULL) {
        perror("Error opening file for writing (are you running with sudo?)");
        return -1;
    }
    fprintf(fp, "%d", value);
    fclose(fp);
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <mode> [value]\n", argv[0]);
        fprintf(stderr, "  Mode 0: Get current brightness (prints percentage)\n");
        fprintf(stderr, "    Example: %s 0\n", argv[0]);
        fprintf(stderr, "  Mode 1: Set brightness to percentage\n");
        fprintf(stderr, "    Example: %s 1 75\n", argv[0]);
        return 1;
    }

    char device[64];
    if (find_backlight_device(device, sizeof(device)) != 0) {
        return 1;
    }

    char max_brightness_path[256];
    char brightness_path[256];
    snprintf(max_brightness_path, sizeof(max_brightness_path), "%s%s/max_brightness", BACKLIGHT_PATH, device);
    snprintf(brightness_path, sizeof(brightness_path), "%s%s/brightness", BACKLIGHT_PATH, device);

    int max_brightness = read_int_from_file(max_brightness_path);
    if (max_brightness <= 0) {
        fprintf(stderr, "Error: Could not read a valid max_brightness.\n");
        return 1;
    }

    int mode = atoi(argv[1]);

    if (mode == 0) {
        // --- GET MODE ---
        if (argc != 2) {
            fprintf(stderr, "Error: Mode 0 requires no other arguments.\n");
            return 1;
        }
        int current_brightness = read_int_from_file(brightness_path);
        if (current_brightness < 0) {
            fprintf(stderr, "Error: Could not read current brightness.\n");
            return 1;
        }
        // Calculate and print the percentage
        int percentage = (int)(((float)current_brightness / (float)max_brightness) * 100.0);
        printf("%d\n", percentage); // Print *only* the percentage number

    } else if (mode == 1) {
        // --- SET MODE ---
        if (argc != 3) {
            fprintf(stderr, "Error: Mode 1 requires a percentage value.\n");
            return 1;
        }
        int percentage = atoi(argv[2]);
        if (percentage < 0 || percentage > 100) {
            fprintf(stderr, "Error: Percentage must be between 0 and 100.\n");
            return 1;
        }
        int new_brightness = (int)(((float)percentage / 100.0) * max_brightness);
        if (write_int_to_file(brightness_path, new_brightness) != 0) {
            return 1;
        }
        printf("Brightness set to %d%%\n", percentage);

    } else {
        fprintf(stderr, "Error: Invalid mode. Use 0 (get) or 1 (set).\n");
        return 1;
    }

    return 0;
}