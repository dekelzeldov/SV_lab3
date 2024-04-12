import itertools;

from .util import cached_property;

class State(object):
    """
    Abstract state object.
    """
    def __init__(self, model):
        self.model = model;

    def __hash__(self):
        return hash(tuple(self));

    def __eq__(self, other):
        return all(x==y for x, y in zip(self, other));

    def clone(self):
        """
        Returns a copy of this state that may be modified.
        """
        return NotImplementedError;

    @property
    def labels(self):
        """
        Returns a set of all state labels applicable in this state.
        """
        raise NotImplementedError;

class StateLabel(object):
    """
    Abstract state label object.
    """
    def __init__(self, model, id):
        self.model = model;
        self.id = id;

        self.NDS = None;
        self.coenable = None;
        self.tests = None;

        # NES cost
        self.cost = 0;

    def __repr__(self):
        return "StateLabel(%s)" % repr(self.id);

    @cached_property
    def NES(self):
        """
        Returns the necessary enabling set for this label.
        """
        if(self.tests is None):
            return None;

        return set(act for act in self.model.actions
                   if not self.tests.isdisjoint(act.writes));

class Action(object):
    """
    Abstract action object.
    """
    def __init__(self, model, id):
        self.model = model;
        self.id = id;

        self.guards = set();

        # reduction information
        self.commute = None;

        # affect sets
        self.reads = None;
        self.writes = None;

        # stubborn score
        self._score = 0;

    def __repr__(self):
        return "Action(%s)" % repr(self.id);

    @cached_property
    def coenable(self):
        """
        Returns the coenable set of all labels in this action,
         or None if this information is not provided.
        """
        gs = itertools.chain.from_iterable(g.coenable for g in self.guards);
        try:
            return set(gs);
        except TypeError:
            return None;

    @cached_property
    def vars(self):
        """
        Returns the variable set of this action,
         or None if this information is not provided.
        """
        try:
            return set(itertools.chain(self.tests, self.reads, self.writes));
        except TypeError:
            return None;

    @cached_property
    def tests(self):
        """
        Returns the test set of this action,
         or None if this information is not provided.
        """
        gt = itertools.chain.from_iterable(g.tests for g in self.guards);
        try:
            return set(gt);
        except TypeError:
            return None;

    def accords(self, other):
        """
        Returns whether this action accords with another action [other].
        """
        assert(isinstance(other, Action));
        # only use DNA if we know it won't call us
        if("DNA" in self.__dict__ and (other in self.DNA)):
            return False;

        """
        TODO (por lab): implement the three forms of accordance.
        BEGIN-CUT-CODE
        """

        # accordance based on shared variables
        if(self.vars and other.vars):
            vs = self.vars.intersection(other.vars);
            ws = set.union(self.writes, other.writes);
            if(vs.isdisjoint(ws)):
                return True;

        # accordance based on co-enabledness
        if(self.coenable and other.guards.isdisjoint(self.coenable)):
            return True;

        # accordance based on commutation
        if(self.commute and other in self.commute):
            return True;
        """
        END-CUT-CODE
        """
        return False;

    @cached_property
    def DNA(self):
        """
        Returns the do-not-accord set of this action.
        """
        return set(act for act in self.model.actions
                   if not self.accords(act));

    @cached_property
    def enables(self):
        """
        Returns the set of guards enabled by this action.
        """
        # first call to enables will initialize all actions
        for act in self.model.actions:
            act.enables = set();

        for lbl in self.model.labels:
            for act in lbl.NES:
                act.enables.add(lbl);

        return self.enables;

    @property
    def score(self):
        """
        Return the current score for this action.
        """
        return self._score;

    @score.setter
    def score(self, v):
        """
        Set the current score of this action to [v] and update NESes.
        """
        old = self._score;
        self._score = v;

        diff = v - old;
        if(diff==0):
            return;

        # update NES cost for all guards
        for lbl in self.enables:
            lbl.cost += diff;

class Model(object):
    """
    Abstract model object.
    """
    name = "(unnamed)";
    initialState = None;

    StateSet = set;

    def __init__(self):
        self.actions = self.Actions(self, Action);
        self.labels = self.Labels(self, StateLabel);

    class AttrPool(object):
        """
        Object to allocate named objects on demand.
        """
        def __init__(self, model, type=None):
            self.data = {};
            self.model = model;
            self.type = type;

        def __repr__(self):
            return repr(self.data);

        def __len__(self):
            return len(self.data);

        def __getitem__(self, key):
            return self.data[key];

        def __iter__(self):
            return iter(self.data.values());

        def get(self, key):
            if(key in self.data):
                return self.data[key];

            v = self.type(self.model, key);
            self.data[key] = v;
            return v;

        def add(self, id, props=None):
            """
            Add a new item named [id] with given properties [props].
            """
            mdl = self.model;
            item = self.get(id);
            if(props is None):
                return;

            # convert property dict to actual properties
            for prop, (dst, src) in self.propMap.items():
                v = props.get(prop, None);
                if(v is None):
                    continue;
                if(src):
                    v = (getattr(mdl, src).get(i) for i in v);
                setattr(item, dst, set(v));

        def update(self, items):
            """
            Add the items from a dict [items] of names to properties.
            """
            for i, v in items.items():
                self.add(i, v);

    class Actions(AttrPool):
        """
        Collection of action objects.
        """
        propMap = {
            "DNA":      ("DNA", "actions"),
            "commute":  ("commute", "actions"),
            "guards":   ("guards", "labels"),
            "reads":    ("reads", None),
            "writes":   ("writes", None),
        };

    class Labels(AttrPool):
        """
        Collection of label objects.
        """
        propMap = {
            "NES":      ("NES", "actions"),
            "NDS":      ("NDS", "actions"),
            "coenable": ("coenable", "labels"),
            "tests":    ("tests", None),
        };

    def nextStates(self, src):
        """
        Returns for each successor state of [src] a tuple consisting of the
         state object and the action used to get there.
        """
        raise NotImplementedError;

    def enabled(self, src):
        """
        Returns a tuple consisting of the set of all enabled actions from
         state [src], and a sample action.
        """
        en, some = set(), None;
        labels = src.labels;
        for act in self.actions:
            # are all of the action's guards enabled?
            if(not labels.issuperset(act.guards)):
                act.score = 1;
                continue;

            act.score = len(self.actions);
            en.add(act);
            if(some is None):
                some = act;

        return (en, some);

    def stubborn(self, src):
        """
        Returns a set of the (enabled) stubborn set for a state [src].
        """
        stubborn = set();
        en, some = self.enabled(src);
        if(some is None):
            return stubborn;

        labels = src.labels;
        queue = {some};
        while queue:
            """
            TODO (por lab): implement the stubborn set algorithm.
            BEGIN-CUT-CODE
            """
            cur = queue.pop();
            cur.score = 0;

            stubborn.add(cur);

            if(cur in en):
                # add set of all non-according actions
                queue.update(cur.DNA - stubborn);
            else:
                # add the necessary enabling set for one non-enabled guard
                best = None;
                for g in cur.guards:
                    if(g in labels):
                        continue;

                    if(best is None or g.cost < best.cost):
                        best = g;

                    if(best.cost==0):
                        break;

                assert(best is not None);
                queue.update(best.NES - stubborn);
            """
            END-CUT-CODE
            """

        return stubborn.intersection(en);

    def reach(self, dead=None, live=None):
        """
        Iterate through reachable statespace. Adds deadlock states to [dead],
         and livelock states to [live].
        Returns each reachable state.
        """
        visited = self.StateSet();
        stack = [self.initialState];
        while stack:
            cur = stack.pop();
            # check if this state was already visited
            if(cur in visited):
                continue;

            # visit all successor states
            succ = 0;
            for i, _ in self.nextStates(cur):
                stack.append(i);
                succ += 1;

            # record dead- and livelocks
            if(dead is not None and succ==0):
                dead.add(cur);
            if(live is not None and succ==1 and stack[-1]==cur):
                live.add(cur);

            if(cur is not None):
                visited.add(cur);
                yield cur;
