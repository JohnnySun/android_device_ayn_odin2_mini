#include <errno.h>
#include <fcntl.h>
#include <linux/magic.h>
#include <linux/reboot.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <sys/statfs.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#define TIMEOUT_SECONDS 90
#define REAL_INIT "/init.real"
#define TRACE_PATH "/metadata/odin-first-stage-kmsg.log"
#define PENDING_CAPACITY (512 * 1024)

static char pending[PENDING_CAPACITY];
static size_t pending_size;

static int write_all(int fd, const void* data, size_t length) {
    const char* cursor = data;
    while (length > 0) {
        const ssize_t written = write(fd, cursor, length);
        if (written < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        cursor += written;
        length -= (size_t)written;
    }
    return 0;
}

static void kmsg(const char* message) {
    const int fd = open("/dev/kmsg", O_WRONLY | O_CLOEXEC);
    if (fd < 0) return;
    const size_t length = strlen(message);
    if (write(fd, message, length) < 0) {
        // The timeout path must continue even when early logging is unavailable.
    }
    close(fd);
}

static void retain_pending(const char* data, size_t length) {
    if (length >= sizeof(pending)) {
        memcpy(pending, data + length - sizeof(pending), sizeof(pending));
        pending_size = sizeof(pending);
        return;
    }
    if (pending_size + length > sizeof(pending)) {
        const size_t discard = pending_size + length - sizeof(pending);
        memmove(pending, pending + discard, pending_size - discard);
        pending_size -= discard;
    }
    memcpy(pending + pending_size, data, length);
    pending_size += length;
}

static int metadata_is_mounted(void) {
    struct statfs info;
    return statfs("/metadata", &info) == 0 && (unsigned long)info.f_type == F2FS_SUPER_MAGIC;
}

static int open_trace(void) {
    if (!metadata_is_mounted()) return -1;
    const int fd = open(TRACE_PATH, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC | O_DSYNC, 0600);
    if (fd < 0) return -1;
    if (pending_size > 0 && write_all(fd, pending, pending_size) != 0) {
        close(fd);
        return -1;
    }
    pending_size = 0;
    return fd;
}

static int deadline_reached(const struct timespec* deadline) {
    struct timespec now;
    if (clock_gettime(CLOCK_BOOTTIME, &now) != 0) return 0;
    return now.tv_sec > deadline->tv_sec ||
           (now.tv_sec == deadline->tv_sec && now.tv_nsec >= deadline->tv_nsec);
}

static void capture_until_deadline(void) {
    struct timespec deadline = {0};
    const int has_boot_clock = clock_gettime(CLOCK_BOOTTIME, &deadline) == 0;
    int fallback_polls = TIMEOUT_SECONDS * 10;
    if (has_boot_clock) {
        deadline.tv_sec += TIMEOUT_SECONDS;
    }

    int input = open("/dev/kmsg", O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    int output = -1;
    static const char start[] = "odin_init_timeout: first-stage capture started\n";
    retain_pending(start, sizeof(start) - 1);

    while (has_boot_clock ? !deadline_reached(&deadline) : fallback_polls-- > 0) {
        if (output < 0) output = open_trace();

        if (input >= 0) {
            char buffer[8192];
            const ssize_t count = read(input, buffer, sizeof(buffer));
            if (count > 0) {
                if (output >= 0) {
                    if (write_all(output, buffer, (size_t)count) != 0) {
                        close(output);
                        output = -1;
                    }
                } else {
                    retain_pending(buffer, (size_t)count);
                }
                continue;
            }
            if (count < 0 && errno != EINTR && errno != EAGAIN) {
                close(input);
                input = -1;
            }
        }

        struct pollfd poll_fd = {.fd = input, .events = POLLIN};
        poll(&poll_fd, input >= 0 ? 1 : 0, 100);
    }

    static const char expired[] = "odin_init_timeout: boot deadline expired; rebooting to bootloader\n";
    if (output >= 0) {
        write_all(output, expired, sizeof(expired) - 1);
        fsync(output);
        close(output);
    }
    if (input >= 0) close(input);
}

static void timeout_child(void) {
    capture_until_deadline();
    kmsg("odin_init_timeout: boot deadline expired; rebooting to bootloader\n");
    sync();
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_RESTART2, "bootloader");
    syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
            LINUX_REBOOT_CMD_RESTART, NULL);
    _exit(125);
}

int main(int argc, char** argv) {
    if (argc == 2 && strcmp(argv[1], "--print-config") == 0) {
        printf("timeout_seconds=%d real_init=%s\n", TIMEOUT_SECONDS, REAL_INIT);
        return 0;
    }

    const pid_t child = fork();
    if (child == 0) timeout_child();
    if (child < 0) kmsg("odin_init_timeout: fork failed; continuing without deadline\n");

    argv[0] = (char*)REAL_INIT;
    execv("/init.real", argv);
    kmsg("odin_init_timeout: exec /init.real failed\n");
    return 127;
}
