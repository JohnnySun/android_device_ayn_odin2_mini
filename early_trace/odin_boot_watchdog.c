#include <errno.h>
#include <fcntl.h>
#include <linux/reboot.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#define TIMEOUT_SECONDS 180
#define TRACE_PATH "/metadata/odin-boot-watchdog.log"

static int write_all(int fd, const char* data, size_t length) {
    while (length > 0) {
        const ssize_t written = write(fd, data, length);
        if (written < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        data += written;
        length -= (size_t)written;
    }
    return 0;
}

static void record(const char* message) {
    const int fd = open(TRACE_PATH, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC | O_DSYNC, 0600);
    if (fd < 0) return;
    write_all(fd, message, strlen(message));
    fsync(fd);
    close(fd);
}

static void wait_for_deadline(void) {
    struct timespec deadline;
    if (clock_gettime(CLOCK_BOOTTIME, &deadline) != 0) {
        sleep(TIMEOUT_SECONDS);
        return;
    }
    deadline.tv_sec += TIMEOUT_SECONDS;
    while (clock_nanosleep(CLOCK_BOOTTIME, TIMER_ABSTIME, &deadline, NULL) == EINTR) {
    }
}

int main(int argc, char** argv) {
    if (argc == 2 && strcmp(argv[1], "--print-config") == 0) {
        printf("timeout_seconds=%d recovery_target=bootloader\n", TIMEOUT_SECONDS);
        return 0;
    }
    if (argc != 1) return 2;

    record("watchdog armed: bootloader recovery in 180 seconds\n");
    wait_for_deadline();
    record("watchdog expired: rebooting to bootloader\n");
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_RESTART2, "bootloader");
    record("watchdog recovery failed: restart2 returned\n");
    return 125;
}
