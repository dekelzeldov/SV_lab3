# PINS interface
The `model.pins.Model` object allows creation of a model from a PINS plugin.
The PINS interface calls are implemented in Python, using the `ctypes` library.

A PINS model can be created as follows:

    import model.pins;
    mdl = model.pins.Model("./path/to/pins/plugin.so");

On the Python side, `model.pins.Model` is a regular `model.Model`-class object.
Its responsibility is to represent the Python view of the model. It creates a
`model.pins.pins.Model` to communicate with the PINS model.

On the PINS side, the `model.pins.pins.Model` represents a PINS view of the
model. This model creates a `model.pins.pins.Wrapper`, which loads a C wrapper
library (`wrapper.c`) that exposes all available PINS functions. Each function
calls into the `Wrapper.dispatch`, which dispatches the PINS function to the
appropriate Python function in the `model.pins.pins.Model`.

Non-PINS models can be loaded using an appropriate loader, which provides the
appropriate `pins_model_init` function. The loader is automatically determined
from the symbols exported from the plugin: for example, a plugin that exposes
`spins_get_initial_state` is determined to be a SpinS model, and is loaded
using the SpinS loader. This is handled by the `model.pins.pins.Wrapper`.

## `CallbackGenerator`
The PINS next-states callback mechanism is converted into a Python generator;
this is done by the `CallbackGenerator` object. This object makes use of
coroutines if a supported coroutine library (such as `greenlet`) is installed.

While a fallback mechanism is provided, use of a coroutine library is highly
recommended because it allows the `CallbackGenerator` to suspend the PINS
next-state function and emit each successor one at a time. The fallback first
collects all successors and then emits them; this requires storing the entire
set of successors (of which there may be many) and creates a delay before the
first successor is emitted. Making use of coroutines avoids these drawbacks.
