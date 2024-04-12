import copy;

from . import model;

class SlotState(model.State):
    """
    Slot-based state object.
    """
    def __init__(self, model, names, data=None):
        """
        Create a new state for a [model] with slots with given [names]. Slots
         can optionally be initialized with [data].
        """
        super().__init__(model);
        self.names = names;
        if(data is None):
            data = [0] * len(names);
        self.slots = data;

    def __repr__(self):
        l = [];
        for i, v in enumerate(self.slots):
            l.append(repr(self.names[i]) + ": " + repr(v));
        return "{" + ", ".join(l) + "}";

    def __len__(self):
        return len(self.slots);

    def __getitem__(self, n):
        return self.slots[self.names.index(n)];

    def __setitem__(self, n, v):
        self.slots[self.names.index(n)] = v;

    def __iter__(self):
        return iter(self.slots);

    def __hash__(self):
        return super().__hash__();

    def __eq__(self, other):
        same = (self.slots==other.slots);
        same = same or super().__eq__(other);
        return (self.names is other.names) and same;

    def clone(self):
        """
        Returns a copy of this state that may be modified.
        """
        slots = copy.copy(self.slots);
        return type(self)(self.model, self.names, slots);
