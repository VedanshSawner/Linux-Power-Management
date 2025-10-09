#include <stdio.h>
#include <libnotify/notify.h>

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <\"Summary\"> <\"Body Message\">\n", argv[0]);
        return 1;
    }

    if (!notify_init("BatteryManager")) {
        fprintf(stderr, "Failed to initialize libnotify.\n");
        return 1;
    }

    
    // NotifyNotificationClass *n = notify_notification_new(argv[1], argv[2], "dialog-information");
    NotifyNotification *n = notify_notification_new(argv[1], argv[2], "dialog-information");
    notify_notification_show(n, NULL);

    g_object_unref(G_OBJECT(n));
    notify_uninit();

    return 0;
}