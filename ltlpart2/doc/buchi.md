# Büchi automata
The framework supports model checking using Büchi automata. The
`buchi.Automaton` class represents a generalized Büchi automaton. Such an
automaton can be created manually, or from an LTL formula.

## LTL
The file `ltl.py` contains a parser for LTL expressions. The function
`ltl.parse(s)` parses a formula expressed as a string and returns the syntax
tree.

While constructing the syntax tree, the parser also transforms the formula into
negation normal form; in this form, the negation operator may only appear
before literals. This form is expected by the algorithm used to create a Büchi
automata from an LTL formula.

## Cross product
To use a Büchi automata with a `Model`-class model, the cross product can be
created using the class `buchi.Product`. This class is itself a `Model`, and
generates the cross product on-the-fly in its `nextStates`.

The `Product` class also provides the function `hasCycle`, which determines
if the product has an accepting cycle.
