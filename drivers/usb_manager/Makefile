CC = gcc
CFLAGS = -Wall -Wextra
TARGET_NAME = usb_manager_tool
OUTPUT_DIR = ../../bin
TARGET = $(OUTPUT_DIR)/$(TARGET_NAME)
SRC = usb_manager_tool.c

all: $(TARGET)

$(TARGET): $(SRC)
	@mkdir -p $(OUTPUT_DIR)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)
	@echo "Compiled $(SRC) -> $(TARGET)"

clean:
	rm -f $(TARGET)