CFLAGS += -std=c99 -Wall -pedantic -g --shared -fPIC

.PHONY: all clean

all: wrapper.so loader-spins.so

%.so: %.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f *.so
