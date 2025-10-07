# Makefile for the webcam C tool

CC = gcc
CFLAGS = -Wall -Wextra

TARGET_NAME = webcam_tool
OUTPUT_DIR = ../../bin
TARGET = $(OUTPUT_DIR)/$(TARGET_NAME)
SRC = webcam_tool.c

all: $(TARGET)

$(TARGET): $(SRC)
	@mkdir -p $(OUTPUT_DIR)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)
	@echo "Compiled $(SRC) -> $(TARGET)"

clean:
	rm -f $(TARGET)
