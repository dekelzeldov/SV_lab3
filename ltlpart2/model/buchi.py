from . import ltl;
from . import model;

# Gerth, R.; Peled, D.; Varde, M. Y. et al. "Simple On-the-fly Automatic
# Verification of Linear Temporal Logic". IFIP Advances in Information and
# Communication Technology (1995): 3--18.

# Schwoon, S.; Esparza, J. "A Note on On-The-Fly Verification Algorithms".
# Lecture Notes in Computer Science, vol. 3440 (2005): 174--190.

class TableauNode(object):
    """
    Tableau node object.
    """
    def __init__(self, incoming, new=[], old=[], next=[]):
        self.incoming = set(incoming);

        self.new = set(new);
        self.old = set(old);
        self.next = set(next);

        self.buchiNode = Automaton.State();

    def freeze(self):
        self.old = frozenset(self.old);
        self.next = frozenset(self.next);

    @property
    def key(self):
        if(not isinstance(self.old, frozenset)):
            self.freeze();
        return (self.old, self.next);

    def clone(self):
        return TableauNode(self.incoming, self.new, self.old, self.next);

class Automaton(object):
    """
    Labeled generalized Büchi automaton.
    """
    class State(object):
        def __init__(self):
            self.outgoing = set();
            self.labels = set();

        def eval(self, lbl):
            """
            Evaluate if the labels of a state match a given set of labels
             [lbl].
            """
            for l in self.labels:
                if(l.op=="value"):
                    if(l.args[0] not in lbl):
                        return False;

                elif(l.op=="not"):
                    if(l.args[0].args[0] in lbl):
                        return False;

                else:
                    raise NotImplementedError;

            return True;

    def __init__(self):
        self.init = None;
        self.states = set();
        self.accept = [];

    @classmethod
    def fromLTL(cls, expr):
        """
        Returns the Büchi automaton for an LTL expression [expr].
        """
        assert(isinstance(expr, ltl.Expression));
        init = TableauNode([]);

        # nodes are indexed by TableauNode.key (= the tuple (old, next))
        nodes = {};
        stack = [TableauNode([init], [expr])];
        while(stack):
            n = stack.pop();

        """
        TODO (LTL lab): implement the Gerth algorithm.

            m = n.new.pop();
            if(m.op==...):
                ....
            elif(m.op==...):
                
            else:
                raise NotImplementedError(m.op);

        """
            stack.append(n);

        # prepare accept sets
        def subexpr(expr, lst):
            """
            Collect all until-subexpressions of [expr] into the list [lst].
            Returns [lst].
            """
            if(not isinstance(expr, ltl.Expression)):
                return lst;
            if(expr.op=="until"):
                lst.append(expr);
            for a in expr.args:
                subexpr(a, lst);
            return lst;

        accept = {u: set() for u in subexpr(expr, [])};

        # convert tableau nodes to Büchi nodes
        for n in nodes.values():
            # convert incoming to outgoing arrows
            for inc in n.incoming:
                inc.buchiNode.outgoing.add(n.buchiNode);

            # convert labels
            for expr in n.old:
                if(expr.op in ["not", "value"]):
                    n.buchiNode.labels.add(expr);

            # add to accept sets
            for until, acc in accept.items():
                if((until not in n.old) or (until.args[1] in n.old)):
                    acc.add(n.buchiNode);

        # return the resulting Büchi automaton
        buchi = cls();
        buchi.init = init.buchiNode;
        buchi.states = set(n.buchiNode for n in nodes.values());

        if(len(accept) > 0):
            buchi.accept = list(frozenset(a) for a in accept.values());
        else:
            # if there is no accept set, all cycles are accepting
            buchi.accept = [frozenset(buchi.states)];

        return buchi;

class Product(model.Model):
    """
    Büchi product model object.

    Represents the cross product of a Büchi automaton [buchi] and a model
     [model].
    """
    class State(model.State):
        __slots__ = ["bState", "mState", "accept"];
        def __init__(self, model, b, m, a):
            super().__init__(model);

            self.bState = b;
            self.mState = m;

            # current accept set (counting construction)
            self.count = a;

        def __iter__(self):
            yield self.bState;
            yield self.mState;
            yield self.count;

        def __repr__(self):
            return "Product.State(%s, %s, %s)" \
                    % (self.bState, self.mState, self.count);

        @property
        def labels(self):
            """
            Returns a set of all state labels applicable in this state.
            """
            mdl = self.model;

            labels = set();
            if(self.count==0 and (self.bState in mdl.buchi.accept[0])):
                labels.add("accept");

            return {mdl.labels[v] for v in labels};

        @property
        def accepting(self):
            """
            Returns whether this state is accepting.
            """
            return self.model.labels["accept"] in self.labels;

    def __init__(self, buchi, model):
        super().__init__();

        self.buchi = buchi;
        self.model = model;

        self.labels.add("accept");

        self.initialState = None;

    def nextStates(self, src):
        """
        Returns for each successor state of [src] a tuple consisting of the
         state object and the action used to get there.
        """
        nextStates = None;
        outgoing = None;
        count = 0;
        if(src is None):
            nextStates = [(self.model.initialState, None)];
            outgoing = self.buchi.init.outgoing;
        else:
            nextStates = self.model.nextStates(src.mState);
            outgoing = src.bState.outgoing;
            count = src.count;

        # product has (q, s) ={a}> (p, t) if s ={a}> t and q ={L(t)}> p
        accepts = self.buchi.accept;
        for s, a in nextStates:
            lbl = set(l.id for l in s.labels);

            for b in outgoing:
                if(not b.eval(lbl)):
                    continue;

                if(b in accepts[count]):
                    count = (count + 1) % len(accepts);

                yield (Product.State(self, b, s, count), a);

    def hasCycle(self):
        """
        Determine whether this Büchi automaton has an accepting cycle.
        Returns the cycle,
         or None if no such cycle exists.
        """
        class Color:
            WHITE = 0;
            CYAN  = 1;
            BLUE  = 2;
            RED   = 3;

        # the stack is managed manually for easy return of cycles
        stack = [];
        color = {};

        def blue(s):
            stack.append(s);
            """
            TODO (LTL lab): implement blue phase of NDFS.

            Tip: you can use `color.get(node, Color.WHITE)` to get the color
            of a given `node`, or the default value "white" if that node hasn't
            been colored yet.
            """
            stack.pop();

        def red(s):
            stack.append(s);
            """
            TODO (LTL lab): implement red phase of NDFS.
            """
            stack.pop();

        for i, _ in self.nextStates(self.initialState):
            try:
                blue(i);
            except AssertionError:
                return stack;

        return None;
