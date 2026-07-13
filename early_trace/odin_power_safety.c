#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define LOG_PATH "/metadata/odin-power-safety.log"
#define POLICY_ROOT "/sys/devices/system/cpu/cpufreq"

static const char* const kPolicies[] = {"policy0", "policy3", "policy7"};

static int write_all(int fd, const char* data, size_t length) {
    while (length > 0) {
        const ssize_t written = write(fd, data, length);
        if (written < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (written == 0) {
            errno = EIO;
            return -1;
        }
        data += written;
        length -= (size_t)written;
    }
    return 0;
}

static int read_text(const char* path, char* value, size_t capacity) {
    if (capacity < 2) return -1;
    const int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    const ssize_t count = read(fd, value, capacity - 1);
    close(fd);
    if (count <= 0) return -1;
    value[count] = '\0';
    size_t length = (size_t)count;
    while (length > 0 && (value[length - 1] == '\n' || value[length - 1] == '\r')) {
        value[--length] = '\0';
    }
    return 0;
}

static bool has_token(const char* list, const char* expected) {
    const size_t expected_length = strlen(expected);
    const char* cursor = list;
    while (*cursor != '\0') {
        while (*cursor == ' ' || *cursor == '\t' || *cursor == '\n' || *cursor == '\r') cursor++;
        const char* start = cursor;
        while (*cursor != '\0' && *cursor != ' ' && *cursor != '\t' && *cursor != '\n' &&
               *cursor != '\r') {
            cursor++;
        }
        if ((size_t)(cursor - start) == expected_length &&
            strncmp(start, expected, expected_length) == 0) {
            return true;
        }
    }
    return false;
}

static int policy_index(const char* name) {
    for (size_t i = 0; i < sizeof(kPolicies) / sizeof(kPolicies[0]); i++) {
        if (strcmp(name, kPolicies[i]) == 0) return (int)i;
    }
    return -1;
}

static bool exact_policy_set(void) {
    bool seen[sizeof(kPolicies) / sizeof(kPolicies[0])] = {false};
    DIR* dir = opendir(POLICY_ROOT);
    if (dir == NULL) return false;
    bool valid = true;
    struct dirent* entry;
    while ((entry = readdir(dir)) != NULL) {
        if (strncmp(entry->d_name, "policy", 6) != 0) continue;
        const int index = policy_index(entry->d_name);
        if (index < 0 || seen[index]) {
            valid = false;
            break;
        }
        seen[index] = true;
    }
    closedir(dir);
    if (!valid) return false;
    for (size_t i = 0; i < sizeof(seen) / sizeof(seen[0]); i++) {
        if (!seen[i]) return false;
    }
    return true;
}

static int append_log(int fd, const char* policy, const char* before, const char* after, int result) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return -1;
    char line[256];
    const int length = snprintf(line, sizeof(line), "%lld.%09ld %s before=%s after=%s result=%d\n",
                                (long long)now.tv_sec, now.tv_nsec, policy, before, after, result);
    if (length <= 0 || (size_t)length >= sizeof(line)) return -1;
    return write_all(fd, line, (size_t)length);
}

int main(void) {
    const int log_fd = open(LOG_PATH, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC | O_DSYNC, 0600);
    if (log_fd < 0) return 13;
    if (!exact_policy_set()) {
        append_log(log_fd, "guard", "identity-ok", "policy-set-mismatch", 10);
        close(log_fd);
        return 10;
    }

    char governors[sizeof(kPolicies) / sizeof(kPolicies[0])][32];
    for (size_t i = 0; i < sizeof(kPolicies) / sizeof(kPolicies[0]); i++) {
        char path[256];
        char available[512];
        snprintf(path, sizeof(path), POLICY_ROOT "/%s/scaling_available_governors", kPolicies[i]);
        if (read_text(path, available, sizeof(available)) != 0 || !has_token(available, "walt")) {
            append_log(log_fd, kPolicies[i], "available-governors", "missing-walt", 11);
            close(log_fd);
            return 11;
        }
        snprintf(path, sizeof(path), POLICY_ROOT "/%s/scaling_governor", kPolicies[i]);
        if (read_text(path, governors[i], sizeof(governors[i])) != 0 ||
            (strcmp(governors[i], "performance") != 0 && strcmp(governors[i], "walt") != 0)) {
            append_log(log_fd, kPolicies[i], "governor", "unexpected", 12);
            close(log_fd);
            return 12;
        }
    }

    int result = 0;
    for (size_t i = 0; i < sizeof(kPolicies) / sizeof(kPolicies[0]); i++) {
        char path[256];
        char after[32];
        if (strcmp(governors[i], "performance") == 0) {
            snprintf(path, sizeof(path), POLICY_ROOT "/%s/scaling_governor", kPolicies[i]);
            const int fd = open(path, O_WRONLY | O_CLOEXEC);
            if (fd < 0 || write_all(fd, "walt", 4) != 0) {
                if (fd >= 0) close(fd);
                append_log(log_fd, kPolicies[i], governors[i], "write-failed", errno);
                result = 20;
                break;
            }
            close(fd);
        }
        snprintf(path, sizeof(path), POLICY_ROOT "/%s/scaling_governor", kPolicies[i]);
        if (read_text(path, after, sizeof(after)) != 0 || strcmp(after, "walt") != 0) {
            append_log(log_fd, kPolicies[i], governors[i], "readback-failed", errno);
            result = 21;
            break;
        }
        if (append_log(log_fd, kPolicies[i], governors[i], after, 0) != 0) {
            result = 22;
            break;
        }
    }
    fsync(log_fd);
    close(log_fd);
    return result;
}
