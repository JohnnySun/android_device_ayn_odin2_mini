#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define TRACE_PATH "/metadata/odin-early-trace.log"

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

static int open_trace(void) {
    return open(TRACE_PATH, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC | O_DSYNC, 0600);
}

static int append_marker(const char* marker) {
    int fd = open_trace();
    if (fd < 0) return 10;
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
        close(fd);
        return 11;
    }
    char line[512];
    const int length = snprintf(line, sizeof(line), "MARKER %lld.%09ld %s\n",
                                (long long)now.tv_sec, now.tv_nsec, marker);
    if (length <= 0 || (size_t)length >= sizeof(line) ||
        write_all(fd, line, (size_t)length) != 0 || fsync(fd) != 0) {
        close(fd);
        return 12;
    }
    close(fd);
    return 0;
}

static int stream_kmsg(void) {
    int output = open_trace();
    if (output < 0) return 20;
    int input = open("/dev/kmsg", O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    if (input < 0) {
        close(output);
        return 21;
    }
    static const char start[] = "MARKER kmsg-stream-start\n";
    if (write_all(output, start, sizeof(start) - 1) != 0 || fsync(output) != 0) {
        close(input);
        close(output);
        return 22;
    }
    char buffer[8192];
    struct pollfd poll_fd = {.fd = input, .events = POLLIN};
    for (;;) {
        const int ready = poll(&poll_fd, 1, 1000);
        if (ready < 0) {
            if (errno == EINTR) continue;
            break;
        }
        if (ready == 0) {
            fsync(output);
            continue;
        }
        const ssize_t count = read(input, buffer, sizeof(buffer));
        if (count < 0) {
            if (errno == EINTR || errno == EAGAIN) continue;
            break;
        }
        if (count == 0 || write_all(output, buffer, (size_t)count) != 0) break;
        fsync(output);
    }
    close(input);
    close(output);
    return 23;
}

int main(int argc, char** argv) {
    if (argc == 3 && strcmp(argv[1], "--metadata-marker") == 0) {
        return append_marker(argv[2]);
    }
    if (argc == 2 && strcmp(argv[1], "--metadata-kmsg") == 0) {
        return stream_kmsg();
    }
    fprintf(stderr, "usage: %s --metadata-marker MARKER | --metadata-kmsg\n", argv[0]);
    return 2;
}
