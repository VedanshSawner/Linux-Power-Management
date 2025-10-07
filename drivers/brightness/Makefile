# Makefile for the brightness C tool

# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra

# Target executable name
TARGET_NAME = brightness_tool
# Path to the output directory, relative to this Makefile
OUTPUT_DIR = ../../bin

# Target executable path
TARGET = $(OUTPUT_DIR)/$(TARGET_NAME)

# Source file
SRC = brightness_tool.c

all: $(TARGET)

$(TARGET): $(SRC)
	@mkdir -p $(OUTPUT_DIR) # Ensure the bin directory exists
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)
	@echo "Compiled $(SRC) -> $(TARGET)"

clean:
	rm -f $(TARGET)
