class CallbackGenerator(object):
    """
    Iterator for results of a callback function.
    Fallback for systems without a coroutine library.
    """
    name = "fallback";

    def __init__(self, cb):
        self.buf = [];
        self.callback = cb;

    def run(self, *args):
        self.buf.append(args);

    def __iter__(self):
        self.callback(self.run);
        return iter(self.buf);

def init():
    global CallbackGenerator;

    # try Greenlet library
    try:
        import greenlet;
    except ImportError:
        pass;
    else:
        class CallbackGenerator(greenlet.greenlet):
            name = "greenlet";

            def __init__(self, cb):
                self.callback = cb;

            def run(self):
                self.callback(self.parent.switch);

            def __iter__(self):
                return self;

            def __next__(self):
                self.parent = greenlet.getcurrent();
                ret = self.switch();
                if(self.dead):
                    raise StopIteration;
                return ret;
        return;

init();
