import copy;
import types;

from . import model;

def POR(mdl):
    """
    Returns a POR-reduced version of the model [mdl].
    """
    def nextStates(self, src):
        """
        Returns for each POR-reduced successor state of [src] in a [model] a
         tuple consisting of the state object and the action used to get there.
        """
        # stubborn already intersects with enabled
        stubborn = self.stubborn(src);

        for s, t in self.nextStates(src):
            # return only those actions in stubborn set
            if(t in stubborn):
                yield (s, t);

    # create shallow copy and replace nextStates
    m = copy.copy(mdl);
    # XXX: new function bound to original object!
    m.nextStates = types.MethodType(nextStates, mdl);
    return m;
