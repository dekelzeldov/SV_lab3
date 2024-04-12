import ast;

from . import util;

class Tokenizer(util.Tokenizer):
    """
    Tokenizer object.
    """
    _tokens = [
        ("_",         r"[ \t\r\n]+"),
        ("KEYWORD",   r"[()]"),
        ("OP_UNARY",  r"not|next|finally|globally"),
        ("OP_BINARY", r"and|or|until|release"),
        ("PREDICATE", r"[_A-Za-z][_0-9A-Za-z]*|\"(\\.|[^\"])*\""),
        ("INVALID",   r"[^ \t]+")
    ];

class Parser(util.Parser):
    """
    LL(1) parser object.
    """
    # keep ordered s.t. FIRST sets/nullable can be determined in one pass
    _rules = [
        ("#expr-primary", "PREDICATE"),
        ("#expr-primary", "(", "#expr", ")"),

        ("#expr-unary", "#expr-primary"),
        ("#expr-unary", "OP_UNARY", "#expr-unary"),

        ("#expr-binary'",),
        ("#expr-binary'", "OP_BINARY", "#expr-binary"),
        ("#expr-binary", "#expr-unary", "#expr-binary'"),

        ("#expr", "#expr-binary"),

        ("#^", "#expr", None)
    ];

    @util.Parser.Handler("#expr-primary", "PREDICATE")
    def _expr_primary(self, stack, match):
        m = match[0];
        if(m[0]=="\""):
            m = ast.literal_eval(m);

        return Expression("value", m);

    @util.Parser.Handler("#expr-unary", "OP_UNARY")
    def _expr_op_unary(self, stack, match):
        return Expression(match[0], stack.pop());

    @util.Parser.Handler("#expr-binary'", "OP_BINARY")
    def _expr_op_binary(self, stack, match):
        return Expression(match[0], None, stack.pop());

    @util.Parser.Handler("#expr-binary'")
    def _expr_null(self, stack, match):
        # add dummy Expression for later join
        return Expression(None, None);

    @util.Parser.Handler("#expr-binary", "#expr-unary")
    def _expr_join(self, stack, match):
        expr = stack.pop();
        if(expr.op is None):
            return;

        assert(expr.args[0] is None);
        expr.args[0] = stack.pop();
        return expr;

class Expression(object):
    """
    LTL expression object. Expressions are kept in negation normal form.
    """
    exprs = {};

    def __new__(cls, *args):
        op = args[0];
        if(op=="not" and (args[1].op!="value" or args[1]._negate is not None)):
            # push NOT operator inward
            return ~args[1];

        elif(op=="finally"):
            return Expression("until", Expression.TRUE, args[1]);

        elif(op=="globally"):
            return Expression("release", Expression.FALSE, args[1]);

        # ensure only one of each Expression
        if(args not in Expression.exprs):
            Expression.exprs[args] = super().__new__(cls);

        return Expression.exprs[args];

    def __init__(self, op, *args):
        if(hasattr(self, "op")):
            return;

        self.op = op;
        self.args = list(args);

        self._negate = None;
        if(self.op=="not"):
            assert(self.args[0]._negate is None);
            self._negate = self.args[0];
            self.args[0]._negate = self;

    def __repr__(self):
        if(self.op=="value"):
            return repr(self.args[0]);

        if(len(self.args)==1):
            return "%s %s" % (self.op, self.args[0]);

        o = " %s " % self.op;
        o = o.join(repr(v) for v in self.args);
        return "(%s)" % o;

    _dual = {
        "next": "next",
        "and": "or",
        "or": "and",
        "until": "release",
        "release": "until",
    };

    def __invert__(self):
        if(self._negate is not None):
            return self._negate;

        neg = None;
        if(self.op=="value"):
            # only introduce NOT before terminals
            neg = Expression("not", self);

        elif(self.op=="not"):
            # NOT operators have _negate set on init
            assert(False);

        elif(self.op in self._dual):
            neg = Expression(self._dual[self.op], *(~a for a in self.args));

        else:
            raise NotImplementedError;

        self._negate = neg;
        return self._negate;

# set up boolean literals
Expression.TRUE = Expression("value", "true");
Expression.FALSE = Expression("value", "false");
Expression.TRUE._negate = Expression.FALSE;
Expression.FALSE._negate = Expression.TRUE;

def parse(s):
    return Parser(Tokenizer(s)).parse();
