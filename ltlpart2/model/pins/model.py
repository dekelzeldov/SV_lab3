from .. import model;
from .. import slotState;
from ..util import cached_property;

from . import pins;
from . import callback;

class State(slotState.SlotState):
    """
    State object for PINS-based model.
    """
    def __init__(self, model, data=None):
        mdl = model.model;
        assert(isinstance(data, mdl.stateType));
        super().__init__(model, mdl.stateSlots, data);

    def __hash__(self):
        return hash(tuple(self.slots[:]));

    def __eq__(self, other):
        return self.slots[:]==other.slots[:];

    @cached_property
    def labels(self):
        """
        Returns a set of all state labels applicable in this state.
        """
        labels = self.model.model.getStateLabels(self.slots);
        return {self.model._labels[i] for i in labels};

class Model(model.Model):
    """
    PINS-based model object.
    """
    def __init__(self, lib):
        """
        Create a PINS model from a library [lib].
        """
        super().__init__();
        mdl = pins.Model(lib);

        self.name = mdl.wrapper.name;
        self.model = mdl;

        self.initialState = State(self, mdl.initialState);
        # create actions and state labels
        self._actions = [None] * mdl.actionCount;
        acts = self._actions;
        for i in range(mdl.actionCount):
            action = "Action %d" % i;
            if(mdl.actionLabel is not None):
                action = mdl.actionLabel[i];

            acts[i] = self.actions.get(action);

        self._labels = [None] * len(mdl.stateLabels);
        lbls = self._labels;
        for i, v in enumerate(mdl.stateLabels):
            lbls[i] = self.labels.get(v);

        # set up guards
        for i, j in mdl.actionGuards.items():
            ai = acts[i];
            ai.guards.update(lbls[k] for k in j);

        # convert matrices
        slots = mdl.stateSlots;
        matrices = {
            "noAccord":        (acts, acts,  "DNA",      "DNA"),
            "guardNES":        (lbls, acts,  "NES",      None),
            "guardNDS":        (lbls, acts,  "NDS",      None),
            "commute":         (acts, acts,  "commute",  "commute"),
            "coenable":        (lbls, lbls,  "coenable", None),
            "actionRead":      (acts, slots, "reads",    None),
            "actionMayWrite":  (acts, slots, "writes",   None),
            "actionMustWrite": (acts, slots, "writes",   None),
            "guardTest":       (lbls, slots, "tests",    None),
        };

        # create empty sets
        for type, (rows, cols, rowSet, colSet) in matrices.items():
            if(rowSet):
                for r in rows:
                    setattr(r, rowSet, set());
            if(colSet and rows!=cols):
                for c in cols:
                    setattr(c, colSet, set());

        # fill sets
        for type, (rows, cols, rowSet, colSet) in matrices.items():
            mtx = mdl.matrices.get(type, None);
            if(mtx is None):
                continue;
            assert(mtx.n==len(rows) and mtx.m==len(cols));

            for i, j in mtx:
                io, jo = rows[i], cols[j];
                if(rowSet):
                    getattr(io, rowSet).add(jo);
                if(colSet):
                    getattr(jo, colSet).add(io);

    def nextStates(self, src):
        """
        Returns for each successor state of [src] a tuple consisting of the
         state object and the action used to get there.
        """
        mdl = self.model;
        def call(callback):
            mdl.nextStates(src.slots, callback);

        for dst, act in callback.CallbackGenerator(call):
            yield (State(self, dst), self._actions[act]);
