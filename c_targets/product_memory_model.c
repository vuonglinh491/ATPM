#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NAME_LENGTH UINT64_C(100)
#define MAX_ALLOCATION UINT64_C(1048576)
#define INPUT_BUFFER_SIZE 256

typedef struct {
    char operation[16];
    uint64_t first;
    uint64_t second;
} TestCase;

typedef struct {
    char name[MAX_NAME_LENGTH + 1];
    uint64_t price;
    uint64_t stock;
} ProductRecord;

typedef struct {
    const char *status;
    const char *cwe;
    const char *details;
} Result;

static int parse_unsigned(const char *text, uint64_t *value) {
    char *end = NULL;
    unsigned long long parsed;

    if (text == NULL || text[0] == '\0' || text[0] == '-') {
        return 0;
    }
    errno = 0;
    parsed = strtoull(text, &end, 10);
    if (errno == ERANGE || end == text || *end != '\0') {
        return 0;
    }
    *value = (uint64_t)parsed;
    return 1;
}

static int parse_case(char *line, TestCase *test_case) {
    char *first_separator = strchr(line, ',');
    char *second_separator;

    if (first_separator == NULL) {
        return 0;
    }
    *first_separator = '\0';
    second_separator = strchr(first_separator + 1, ',');
    if (second_separator == NULL || strchr(second_separator + 1, ',') != NULL) {
        return 0;
    }
    *second_separator = '\0';

    if (strlen(line) == 0 || strlen(line) >= sizeof(test_case->operation)) {
        return 0;
    }
    strcpy(test_case->operation, line);
    return parse_unsigned(first_separator + 1, &test_case->first)
        && parse_unsigned(second_separator + 1, &test_case->second);
}

static Result analyze_case(const TestCase *test_case) {
    if (strcmp(test_case->operation, "bounded") == 0) {
        ProductRecord product = {0};
        if (test_case->first > MAX_NAME_LENGTH) {
            return (Result){"BLOCKED", "CWE-121", "stack buffer overflow attempt rejected before copy"};
        }
        memset(product.name, 'A', (size_t)test_case->first);
        product.name[test_case->first] = '\0';
        return (Result){"SAFE", "", "name length is within the declared bound"};
    }
    if (strcmp(test_case->operation, "overflow") == 0) {
        if (test_case->first != 0 && test_case->second > UINT64_MAX / test_case->first) {
            return (Result){"BLOCKED", "CWE-190", "allocation size multiplication overflow rejected"};
        }
        return (Result){"SAFE", "", "allocation size multiplication is representable"};
    }
    if (strcmp(test_case->operation, "leak") == 0) {
        if (test_case->second > 1) {
            return (Result){"BLOCKED", "CWE-20", "invalid release flag rejected"};
        }
        if (test_case->first > 0 && test_case->second == 0) {
            return (Result){"DETECTED", "CWE-401", "simulated owned allocations are not released"};
        }
        return (Result){"SAFE", "", "simulated allocations are released"};
    }
    if (strcmp(test_case->operation, "lifecycle") == 0) {
        if (test_case->first == 0) {
            return (Result){"SAFE", "", "no allocation is owned"};
        }
        if (test_case->second == 0) {
            return (Result){"DETECTED", "CWE-401", "owned allocation leaves scope without release"};
        }
        if (test_case->second == 2) {
            return (Result){"DETECTED", "CWE-415", "second release detected by the simulated ownership state"};
        }
        if (test_case->second == 3) {
            return (Result){"DETECTED", "CWE-416", "access after release detected by the simulated ownership state"};
        }
        if (test_case->second == 1) {
            return (Result){"SAFE", "", "allocation is released exactly once"};
        }
        return (Result){"BLOCKED", "CWE-20", "unknown lifecycle operation rejected"};
    }
    if (strcmp(test_case->operation, "type") == 0) {
        if (test_case->first > 1 || test_case->second > 1 || test_case->first != test_case->second) {
            return (Result){"BLOCKED", "CWE-20", "input type does not match the expected field type"};
        }
        return (Result){"SAFE", "", "input type matches the expected field type"};
    }
    if (strcmp(test_case->operation, "null") == 0) {
        if (test_case->first > 1) {
            return (Result){"BLOCKED", "CWE-20", "invalid pointer-presence flag rejected"};
        }
        if (test_case->first == 0) {
            return (Result){"BLOCKED", "CWE-476", "missing required pointer rejected before dereference"};
        }
        return (Result){"SAFE", "", "required pointer is present"};
    }
    if (strcmp(test_case->operation, "allocation") == 0) {
        if (test_case->first > MAX_ALLOCATION) {
            return (Result){"BLOCKED", "CWE-789", "allocation request exceeds the configured cap"};
        }
        return (Result){"SAFE", "", "allocation request is within the configured cap"};
    }
    return (Result){"BLOCKED", "CWE-20", "unknown operation rejected"};
}

int main(void) {
    char line[INPUT_BUFFER_SIZE];
    while (fgets(line, sizeof(line), stdin) != NULL) {
        TestCase test_case = {0};
        Result result;
        size_t length = strlen(line);
        if (length > 0 && line[length - 1] == '\n') {
            line[length - 1] = '\0';
        }
        if (!parse_case(line, &test_case)) {
            puts("INVALID\tCWE-20\tinput record could not be parsed");
            continue;
        }
        result = analyze_case(&test_case);
        printf("%s\t%s\t%s\n", result.status, result.cwe, result.details);
    }
    return ferror(stdin) ? EXIT_FAILURE : EXIT_SUCCESS;
}