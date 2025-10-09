CC = gcc
CFLAGS = -Wall -Wextra `pkg-config --cflags libnotify`
LDFLAGS = `pkg-config --libs libnotify`
TARGET_NAME = notifier_tool
OUTPUT_DIR = ../../bin
TARGET = $(OUTPUT_DIR)/$(TARGET_NAME)
SRC = notifier_tool.c

all: $(TARGET)

$(TARGET): $(SRC)
	@mkdir -p $(OUTPUT_DIR)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)
	@echo "Compiled $(SRC) -> $(TARGET)"

clean:
	rm -f $(TARGET)