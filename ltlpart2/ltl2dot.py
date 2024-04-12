import model;
import model.ltl;
import model.buchi;

import argparse;

def main():
    """
    Draw the Büchi automaton for a given an LTL formula in a dot graph.
    """
    ap = argparse.ArgumentParser(description=main.__doc__);
    ap.add_argument("ltl");
    args = ap.parse_args();

    ltl = model.ltl.parse(args.ltl);
    buchi = model.buchi.Automaton.fromLTL(ltl);

    # determine accept sets for each node
    accept = {};
    for i, v in enumerate(buchi.accept):
        for n in v:
            accept.setdefault(n, set()).add(i);

    def labels(n):
        if(len(n.labels)==0):
            return "True";
        return str(n.labels);

    print("#", args.ltl);
    print("# =", ltl);
    print("digraph{");
    for m in buchi.init.outgoing:
        print("\tinit -> n%x [label=\"%s\"];" % (id(m), labels(m)));

    for n in buchi.states:
        acc = "";
        if(n in accept):
            acc = str(accept[n]);

        print("\tn%x [label=\"%s\"];" % (id(n), acc));
        for m in n.outgoing:
            print("\tn%x -> n%x [label=\"%s\"];" % (id(n), id(m), labels(m)));

    print("}");

if(__name__=="__main__"):
    main();
