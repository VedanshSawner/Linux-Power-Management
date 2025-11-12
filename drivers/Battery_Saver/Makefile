# Makefile for the Battery Saver C tool

CC = gcc
CFLAGS = -Wall -Wextra

# Output binary name
TARGET_NAME = battery_saver_tool
OUTPUT_DIR = ../../bin
TARGET = $(OUTPUT_DIR)/$(TARGET_NAME)

# Source file
SRC = set_power_uconfig.c

all: $(TARGET)

$(TARGET): $(SRC)
	@mkdir -p $(OUTPUT_DIR)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)
	@echo "✅ Compiled $(SRC) -> $(TARGET)"

clean:
	rm -f $(TARGET)
	@echo "🧹 Cleaned $(TARGET)"

