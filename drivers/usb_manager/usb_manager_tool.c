#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CMD_BUFFER_SIZE 512

// Helper function to execute a command and print its output
void run_command(const char* command) {
    FILE *fp = popen(command, "r");
    if (fp == NULL) {
        perror("Failed to run command");
        return;
    }
    char buffer[1024];
    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        printf("%s", buffer);
    }
    pclose(fp);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s list | suspend <location> <port> | resume <location> <port>>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "list") == 0) {
        // We use uhubctl to get a parsable list of devices
        run_command("uhubctl");
    } else if (strcmp(argv[1], "suspend") == 0) {
        if (argc != 4) {
            fprintf(stderr, "Usage: %s suspend <location> <port>\n", argv[0]);
            return 1;
        }
        char command[CMD_BUFFER_SIZE];
        snprintf(command, sizeof(command), "uhubctl -l %s -p %s -a 0", argv[2], argv[3]);
        run_command(command);
    } else if (strcmp(argv[1], "resume") == 0) {
        if (argc != 4) {
            fprintf(stderr, "Usage: %s resume <location> <port>\n", argv[0]);
            return 1;
        }
        char command[CMD_BUFFER_SIZE];
        snprintf(command, sizeof(command), "uhubctl -l %s -p %s -a 1", argv[2], argv[3]);
        run_command(command);
    } else {
        fprintf(stderr, "Unknown command: %s\n", argv[1]);
        return 1;
    }

    return 0;
}