import model;
import model.slotState;

import model.ltl;
import model.buchi;

class State(model.slotState.SlotState):
    @property
    def labels(self):
        """
        Returns a set of all state labels applicable in this state.
        """
        labels = set(i for i in self.names if self[i]);

        mdl = self.model;
        return {mdl.labels[v] for v in labels};

class Model(model.Model):
    """
    Traffic light model object.

    This model is the traffic light example from Principles of Model Checking
     (section 4.4.1). The regular version can guarantee GF(green), the
     energy-saving version cannot.
    """
    name = "Traffic light";
    def __init__(self, eco=False):
        super().__init__();

        s = ["red", "green"];
        self.initialState = State(self, s, data=[True, False]);
        self.eco = eco;

        for i in s:
            self.labels.add(i);

    def nextStates(self, src):
        """
        Returns for each successor state of [src] a tuple consisting of the
         state object and the action used to get there.
        """
        # first process
        dst = src.clone();
        if(src["red"]):
            dst["red"] = False;
            dst["green"] = True;
            yield (dst, None);

            if(self.eco):
                # in eco mode, light may switch off from red
                # this version cannot guarantee GF(green)
                dst = src.clone();
                dst["red"] = False;
                dst["green"] = False;
                yield (dst, None);

        elif(src["green"] or self.eco):
            dst["red"] = True;
            dst["green"] = False;
            yield (dst, None);

        else:
            raise NotImplementedError;

def main():
    # create Büchi automaton
    ltl = model.ltl.parse("not (globally finally green)");
    buchi = model.buchi.Automaton.fromLTL(ltl);

    def check(mdl):
        prod = model.buchi.Product(buchi, mdl);

        # check for cycles
        cyc = prod.hasCycle();
        if(cyc is None):
            print("no cycle");
            return;

        for i, v in enumerate(cyc):
            print(i, v);

    print("# regular stoplight");
    check(Model(eco=False));

    print("\n# eco-friendly stoplight");
    check(Model(eco=True));

if(__name__=="__main__"):
    main();
