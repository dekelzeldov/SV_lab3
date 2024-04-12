import os;
import ctypes as C;

# keep references to all types or they might be garbage collected
ctypes = None;

def init():
    # prepare C types
    t = {};
    t["wrapperCb"] = C.CFUNCTYPE(None, C.c_char_p, C.c_int,
                                 C.POINTER(C.c_void_p));

    t["stateSlot"] = C.c_int;
    t["statePtr"] = C.POINTER(t["stateSlot"]);

    class Action(C.Structure):
        _fields_ = [("labels", C.POINTER(C.c_int)),
                    ("group", C.c_int),
                    ("", C.c_int)];

    t["action"] = C.POINTER(Action);

    class Guard(C.Structure):
        _fields_ = [("length", C.c_int),
                    ("labelID", C.c_int * 0)];

        def toSet(self):
            array = C.cast(C.addressof(self.labelID), C.POINTER(C.c_int));
            return set(array[:self.length]);

    t["guard"] = C.POINTER(Guard);

    t["nextStatesCb"] = C.CFUNCTYPE(None, C.c_void_p, t["action"],
                                    t["statePtr"], C.POINTER(C.c_int));
    t["nextStatesFn"] = C.CFUNCTYPE(C.c_int, C.c_void_p, t["statePtr"],
                                    t["nextStatesCb"], C.c_void_p);

    t["stateLabel"] = C.c_int;
    t["stateLabelFn"] = C.CFUNCTYPE(C.POINTER(t["stateLabel"]), C.c_int,
                                    t["statePtr"]);

    class Matrix(C.Structure):
        _fields_ = [("n", C.c_int),
                    ("m", C.c_int),
                    ("data", C.POINTER(C.c_char))];

        def __iter__(self):
            """
            Returns (row, col) of each nonzero entry in the matrix.
            """
            for i in range(self.n):
                for j in range(self.m):
                    coord = (i, j);
                    if(coord in self):
                        yield coord;

        def __contains__(self, coord):
            i, j = coord;
            return self.data[(self.m * i) + j][0]!=0;

    t["matrix"] = C.POINTER(Matrix);

    return t;

ctypes = init();

class CTypes(object):
    """
    Decorator for C wrapper functions.
    """
    def __init__(self, types):
        self.argtypes = types;

    def __call__(self, func):
        func.argtypes = self.argtypes;
        return func;

class LTSTypeFormat(object):
    DIRECT = 0;
    RANGE = 1;
    CHUNK = 2;
    ENUM = 3;
    BOOL = 4;
    TRILEAN = 5;
    SINT32 = 6;

class LTSType(object):
    """
    LTS type object.
    """
    def __init__(self, name):
        self.name = name;
        self.format = None;
        self.chunks = [];

    @CTypes([C.c_int])
    def setFormat(self, v):
        self.format = v;

    @CTypes([C.c_char_p])
    def addChunk(self, chunk):
        self.chunks.append(chunk);

class Label(object):
    """
    Abstract typed PINS label object.
    """
    def __init__(self, parent):
        self.parent = parent;
        self.name = "";
        self.type = None;

    def __repr__(self):
        return "pins.%s(%s)" % (self.__class__.__name__, repr(self.name));

    def __len__(self):
        return len(self.type.chunks);

    def __getitem__(self, i):
        return self.type.chunks[i];

    @CTypes([C.c_char_p])
    def setName(self, name):
        self.name = name;

    @CTypes([C.c_int])
    def setType(self, tid):
        self.type = self.parent.types[tid];

class EdgeLabel(Label):
    """
    PINS edge label object.
    """
    pass;

class Model(object):
    """
    PINS model object.
    """
    def __init__(self, lib):
        # callback functions
        self._nextStates = None;

        # transition system types
        self.types = {};
        self.matrices = {};

        # state properties
        self.stateSlots = None;
        self.stateType = None;
        self.stateLabels = None;

        # edge properties
        self.edgeLabels = None;

        self.actionCount = 0;
        self.actionLabel = None;
        self.actionGuards = {};

        # create wrapper
        self.wrapper = Wrapper(self, lib);

        if(self.actionLabel is None and len(self.edgeLabels) > 0):
            self.actionLabel = self.edgeLabels[0];
            assert(self.actionCount==len(self.actionLabel));

    @CTypes([C.c_int])
    def setStateLength(self, n):
        self.stateSlots = [None] * n;
        self.stateType = (C.c_int * n);

    @CTypes([C.c_int, C.c_char_p])
    def setStateSlotName(self, n, s):
        self.stateSlots[n] = s;

    @CTypes([ctypes["statePtr"]])
    def setInitialState(self, s):
        self.initialState = self.stateType(*s[0:len(self.stateSlots)]);

    @CTypes([ctypes["nextStatesFn"]])
    def setNextStatesFn(self, fn):
        self._nextStates = fn;

    def nextStates(self, src, callback):
        """
        Calls [callback] for every successor state of [src], with a tuple
         consisting of the state and the action used to get there.
        """
        assert(isinstance(src, self.stateType));
        def convert(ctx, act, dst, copy):
            act = act.contents.group;
            callback(self.stateType(*dst[0:len(self.stateSlots)]), act);

        cb = ctypes["nextStatesCb"](convert);
        self._nextStates(None, src, cb, None);

    # State labels
    @CTypes([C.c_int])
    def setStateLabelCount(self, n):
        self.stateLabels = [None] * n;

    @CTypes([C.c_int, C.c_char_p])
    def setStateLabelName(self, n, s):
        self.stateLabels[n] = s;

    def getStateLabels(self, src):
        """
        Returns a set of all state labels applicable in this state.
        """
        assert(isinstance(src, self.stateType));
        dmax = len(self.stateLabels);
        dst = (ctypes["stateLabel"] * dmax)();

        n = self.wrapper.libWrapper._wrapperGetStateLabels(dst, dmax, src);
        return dst[:n];

    # Edge labels
    @CTypes([C.c_int])
    def setActionCount(self, n):
        self.actionCount = n;

    @CTypes([C.c_int])
    def setActionLabel(self, i):
        self.actionLabel = self.edgeLabels[i];

    @CTypes([C.c_int])
    def setEdgeLabelCount(self, n):
        self.edgeLabels = [EdgeLabel(self) for _ in range(n)];

    @CTypes([C.c_char_p, ctypes["matrix"]])
    def setMatrix(self, kind, mtx):
        mtx = mtx.contents;
        if(self.actionCount <= 0 and (kind=="noAccord" or kind=="actionRead")):
            # use matrix size to set actionCount
            self.actionCount = mtx.n;

        self.matrices[kind] = mtx;

    @CTypes([C.c_int, ctypes["guard"]])
    def setGuards(self, i, guard):
        self.actionGuards[i] = guard[0].toSet();

    @CTypes([C.POINTER(ctypes["guard"])])
    def setGuardsAll(self, guards):
        for i in range(self.actionCount):
            self.setGuards(i, guards[i]);

    @CTypes([C.c_int, C.c_char_p])
    def addType(self, i, name):
        self.types[i] = LTSType(name);

class Wrapper(object):
    """
    PINS wrapper object.
    """
    name = "PINS";

    def __init__(self, model, lib):
        """
        Create a wrapper for a PINS model from a library [lib].
        """
        self.model = model;

        # set up wrapper library
        path = os.path.dirname(os.path.abspath(__file__));
        self.libWrapper = C.CDLL(path + "/wrapper.so", mode=C.RTLD_GLOBAL);

        dispatch = ctypes["wrapperCb"](self.dispatch);
        self.libWrapper._wrapperInit(dispatch);

        # set up model library
        libModel = C.CDLL(lib, mode=C.RTLD_GLOBAL);
        loader = libModel;

        try:
            # try standard PINS interface
            name = str(C.string_at(libModel["pins_plugin_name"]), "ascii");
        except AttributeError:
            # try loaders
            loaders = {
                "spins_get_initial_state": "spins"
            };

            for sym in loaders:
                try:
                    tmp = libModel[sym];
                except AttributeError:
                    continue;
                else:
                    name = loaders[sym];
                    loader = C.CDLL(path + ("/loader-%s.so" % name),
                                    mode=C.RTLD_GLOBAL);
                    break;

        self.name = name;
        self.libModel = libModel;

        loader.pins_model_init();

    def dispatch(self, type, argc, argv):
        """
        Dispatch a PINS function call given by [type], with [argc] arguments
         given in [argv], to the appropriate Python method.
        """
        # [type] is a string representing a method
        type = str(C.string_at(type), "ascii").split(".");

        argi = 0;
        try:
            obj = self.model;
            for attr in type:
                if(attr=="#" or attr=="*"):
                    # use argument as attribute
                    # asterisk means pointer-sized argument
                    cast = C.c_void_p if attr=="*" else C.c_uint;
                    attr = C.cast(argv[argi], C.POINTER(cast))[0];
                    argi += 1;

                    obj = obj[attr];
                else:
                    obj = getattr(obj, attr);
        except AttributeError:
            obj = None;

        if(obj is None):
            raise NotImplementedError(type);

        # cast arguments to appropriate types
        args = [];
        for i in range(argi, argc):
            v = argv[i];
            t = obj.argtypes[i - argi];

            if(t is C.c_int):
                n = C.cast(v, C.POINTER(C.c_int))[0];
            elif(t is C.c_char_p):
                n = str(C.string_at(v), "ascii");
            elif(t is C.c_void_p):
                n = v;
            else:
                n = C.cast(v, t);

            args.append(n);

        # call method
        obj(*args);
