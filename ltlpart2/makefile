.PHONY: all clean

all:
	OS=$$(uname); \
	[ "$$OS" = "Darwin" ] && export CFLAGS="-undefined dynamic_lookup"; \
	cd model/pins && make all

clean:
	cd model/pins && make clean
	
	# remove all cached python bytecode
	f=$$(find . | grep '\.pyc$$'); \
	  [ -n "$$f" ] && rm -v $$f || true
	f=$$(find . | grep '__pycache__$$'); \
	  [ -n "$$f" ] && rmdir -v $$f || true
