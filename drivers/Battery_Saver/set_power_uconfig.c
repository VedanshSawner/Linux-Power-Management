#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <regex.h> 

#define CONF_FILE "/etc/UPower/UPower.conf"
#define TEMP_FILE "/tmp/UPower.conf.tmp"
#define MAX_LINES 1024
#define MAX_LINE_LEN 512

// Helper function to find and replace a setting in the lines array
void replace_or_add(char **lines, int *num_lines, const char *key, const char *value) {
    int key_len = strlen(key);
    int found = 0;
    
    // Create the new line content string
    char new_line_content[MAX_LINE_LEN];
    // Use %s for value, as it covers both percentage strings and action type strings
    snprintf(new_line_content, sizeof(new_line_content), "%s=%s\n", key, value);

    // Iterate and check for replacement
    for (int i = 0; i < *num_lines; i++) {
        // Find the start of the key, ignoring whitespace/comments
        char *start = lines[i];
        while (*start == ' ' || *start == '\t') start++;

        // Check if the line starts with the key followed by '='
        if (strncmp(start, key, key_len) == 0 && start[key_len] == '=') {
            free(lines[i]);
            lines[i] = strdup(new_line_content);
            if (!lines[i]) {
                perror("Memory allocation error during replace");
                exit(EXIT_FAILURE);
            }
            found = 1;
            return; // Replacement done
        }
    }

    // If key not found, add it to the end
    if (!found) {
        if (*num_lines >= MAX_LINES) {
            fprintf(stderr, "Warning: Configuration file exceeds max lines. Could not add new key.\n");
            return;
        }

        lines[*num_lines] = strdup(new_line_content);
        if (!lines[*num_lines]) {
            perror("Memory allocation error during add (strdup)");
            exit(EXIT_FAILURE);
        }
        (*num_lines)++;
    }
}


int main(int argc, char *argv[]) {
    // --- ARGUMENT PARSING RESTORED ---
    // Expects 4 arguments: <low_pct> <critical_pct> <action_pct> <action_type>
    if (argc != 5) {
        fprintf(stderr, "Error: Incorrect number of arguments.\n");
        fprintf(stderr, "Usage: upower_tool <low_pct> <critical_pct> <action_pct> <action_type>\n");
        return 1;
    }

    // The C tool receives all four values as strings from the Python process.
    char *PercentageLow_s = argv[1];
    char *PercentageCritical_s = argv[2];
    char *PercentageAction_s = argv[3];
    char *CriticalPowerAction = argv[4];

    // Simple validation (Optional: Check if percentage strings are valid numbers)
    if (atoi(PercentageLow_s) < 0 || atoi(PercentageLow_s) > 100) {
        fprintf(stderr, "Error: Low Percentage must be between 0 and 100.\n");
        return 1;
    }
    // ---------------------------------
    
    FILE *src, *tmp;
    char *lines[MAX_LINES]; 
    int num_lines = 0;
    char buffer[MAX_LINE_LEN]; 

    // 1. Read the entire configuration file into memory
    src = fopen(CONF_FILE, "r");
    if (!src) {
        perror("Cannot open /etc/UPower/UPower.conf for reading (Check permissions/existence)");
        return 1;
    }
    
    while (fgets(buffer, sizeof(buffer), src) && num_lines < MAX_LINES) {
        lines[num_lines] = strdup(buffer);
        if (!lines[num_lines]) {
            perror("Memory allocation error during read");
            fclose(src);
            return 1;
        }
        num_lines++;
    }
    fclose(src);
    
    // 2. Apply modifications using the DYNAMIC values passed via command line
    replace_or_add(lines, &num_lines, "PercentageLow", PercentageLow_s);
    replace_or_add(lines, &num_lines, "PercentageCritical", PercentageCritical_s);
    replace_or_add(lines, &num_lines, "PercentageAction", PercentageAction_s);
    replace_or_add(lines, &num_lines, "CriticalPowerAction", CriticalPowerAction);

    // 3. Write modified content to the temporary file
    tmp = fopen(TEMP_FILE, "w");
    if (!tmp) {
        perror("Cannot write temporary file");
        for (int i = 0; i < num_lines; i++) free(lines[i]);
        return 1;
    }
    
    for (int i = 0; i < num_lines; i++) {
        fputs(lines[i], tmp);
        free(lines[i]); 
    }
    fclose(tmp);

    // 4. Copy modified file back and restart the service (using sudo via system() calls)
    char copy_command[MAX_LINE_LEN];
    snprintf(copy_command, sizeof(copy_command), "sudo cp %s %s", TEMP_FILE, CONF_FILE);
    
    if (system(copy_command) != 0) {
        fprintf(stderr, "Error: Failed to copy file (check sudo/permissions).\n");
        return 1;
    }
    
    if (system("sudo systemctl restart upower.service") != 0) {
        fprintf(stderr, "Warning: Config written, but failed to restart upower service.\n");
    }
    
    // 5. Clean up temporary file
    if (unlink(TEMP_FILE) != 0) {
        perror("Warning: Failed to delete temporary file");
    }

    printf("✅ UPower thresholds updated successfully with dynamic values!\n");
    return 0;
}
