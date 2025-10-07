#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>

#define BACKLIGHT_PATH "/sys/class/backlight/"

// Helper function to find the first available backlight device name (e.g., "intel_backlight")
int find_backlight_device(char *device_name, size_t len) {
    DIR *d = opendir(BACKLIGHT_PATH);
    if (d == NULL) {
        perror("Failed to open " BACKLIGHT_PATH);
        return -1;
    }

    struct dirent *dir;
    int found = 0;
    while ((dir = readdir(d)) != NULL) {
        // Ignore '.' and '..' directories
        if (strcmp(dir->d_name, ".") != 0 && strcmp(dir->d_name, "..") != 0) {
            strncpy(device_name, dir->d_name, len - 1);
            device_name[len - 1] = '\0';
            found = 1;
            break; // Use the first device found
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
    if (fp == NULL) {
        return -1;
    }
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
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <percentage>\n", argv[0]);
        fprintf(stderr, "Example: %s 75\n", argv[0]);
        return 1;
    }

    int percentage = atoi(argv[1]);
    if (percentage < 0 || percentage > 100) {
        fprintf(stderr, "Error: Percentage must be between 0 and 100.\n");
        return 1;
    }

    char device[64];
    if (find_backlight_device(device, sizeof(device)) != 0) {
        return 1;
    }
    printf("Found backlight device: %s\n", device);

    char max_brightness_path[256];
    char brightness_path[256];
    snprintf(max_brightness_path, sizeof(max_brightness_path), "%s%s/max_brightness", BACKLIGHT_PATH, device);
    snprintf(brightness_path, sizeof(brightness_path), "%s%s/brightness", BACKLIGHT_PATH, device);

    int max_brightness = read_int_from_file(max_brightness_path);
    if (max_brightness <= 0) {
        fprintf(stderr, "Error: Could not read a valid max_brightness from %s\n", max_brightness_path);
        return 1;
    }

    // Calculate the new brightness value
    int new_brightness = (int)(((float)percentage / 100.0) * max_brightness);

    printf("Max brightness: %d, setting to %d (%d%%)\n", max_brightness, new_brightness, percentage);

    if (write_int_to_file(brightness_path, new_brightness) != 0) {
        return 1;
    }

    printf("Brightness set successfully.\n");
    return 0;
}
