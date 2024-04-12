# Model
The `Model` class represents an abstract model. Actual models should be a
subclass of this class. Related to the abstract `Model` is the abstract
`State`. Subclassing the `State` is also a requirement for actual models; a
simple named slot-based state is provided as `SlotState`.

A model is a labeled transition system. A labeled transition system provides
a set of actions, as well as a set of atomic propositions (referred to as
"state labels"). The `Model` class provides access to these actions and
labels by their name: the properties `actions` and `labels` provide dict-like
access to `Action` and `StateLabel` objects.

The `initialState` property gives the initial state for the model. The
`nextStates` function is a generator, which gives all successors to a given
state. For each successor transition, it returns a tuple consisting of the
state and the action.

If the state has been subclassed to provide labels (see also the section
"State"), `Model` provides the function `enabled` to yield the enabled
actions for a given state, and the function `stubborn` to yield the stubborn
set (intersected with the enabled set) for a state.

The function `reach` is a simple DFS-based reachability algorithm, which yields
every reachable state in the model.

## State
Each model must implement its own state class. Models are free to design this
class as they wish, but a state class must be a subclass of the abstract
`State` class. Furthermore, a state class is expected to expose `__hash__` and
`__eq__` methods. A state can access its owner model through the `model`
property.

For models with state labels, the `labels` property (which is implemented as a
getter) for a state must return the set of all applicable state labels as
`StateLabel` objects. These can be retrieved by name from the model's `labels`
property.

State classes can have an `__iter__`: iterating over a state is expected to
yield each value of the state, essentially giving a "serialized" form. The
abstract `State` defines `__hash__` and `__eq__` methods usable by iterable
states. A minimal state class may define only an `__iter__`.
