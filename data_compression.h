#include <stdint.h>
#define TWOS_COMP(x) ((~x) + 1)

void load_uintx(char *bits, int *index, const int x, const uint16_t data);
void load_intx(char *bits, int *index, const int x, const int16_t data);
uint16_t read_uintx(const char *bits, int *index, const int x);
int16_t read_intx(const char *bits, int *index, const int x);
void pack_bits(char *buffer, const char *bits, const int numBits);
void unpack_bits(const char *buffer, char *bits, const int numBits);
