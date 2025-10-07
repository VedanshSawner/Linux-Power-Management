#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>

#define UVC_DRIVER_PATH "/sys/bus/usb/drivers/uvcvideo/"
#define ID_BUFFER_SIZE 32

// Writes the given data string to the specified file path.
int write_to_file(const char *path, const char *data) {
    FILE *fp = fopen(path, "w");
    if (fp == NULL) {
        perror("Error opening file (are you running with sudo?)");
        return -1;
    }
    fprintf(fp, "%s", data);
    fclose(fp);
    return 0;
}

// Scans the uvcvideo driver directory to find the webcam's device ID.
int find_webcam_id(char *id_buffer, size_t len) {
    DIR *d = opendir(UVC_DRIVER_PATH);
    if (d == NULL) {
        perror("Could not open uvcvideo driver directory");
        return -1;
    }

    struct dirent *dir;
    int found = 0;
    while ((dir = readdir(d)) != NULL) {
        if (strchr(dir->d_name, ':') != NULL) {
            char *colon_ptr = strchr(dir->d_name, ':');
            size_t id_len = colon_ptr - dir->d_name;
            if (id_len < len) {
                strncpy(id_buffer, dir->d_name, id_len);
                id_buffer[id_len] = '\0';
                found = 1;
                break;
            }
        }
    }
    closedir(d);
    
    return found ? 0 : -1;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <enable|disable>\n", argv[0]);
        return 1;
    }
    
    char webcam_id[ID_BUFFER_SIZE] = {0};

    if (find_webcam_id(webcam_id, sizeof(webcam_id)) != 0) {
        fprintf(stderr, "Webcam device ID not found. Is it already disabled or unplugged?\n");
        return 1;
    }

    char control_path[256];
    if (strcmp(argv[1], "disable") == 0) {
        printf("Disabling webcam (ID: %s)...\n", webcam_id);
        snprintf(control_path, sizeof(control_path), "%s/unbind", UVC_DRIVER_PATH);
    } else if (strcmp(argv[1], "enable") == 0) {
        printf("Enabling webcam (ID: %s)...\n", webcam_id);
        snprintf(control_path, sizeof(control_path), "%s/bind", UVC_DRIVER_PATH);
    } else {
        fprintf(stderr, "Invalid argument. Use 'enable' or 'disable'.\n");
        return 1;
    }

    if (write_to_file(control_path, webcam_id) != 0) {
        fprintf(stderr, "Failed to %s webcam.\n", argv[1]);
        return 1;
    }

    printf("Webcam %sd successfully.\n", argv[1]);
    return 0;
}
