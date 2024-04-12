import re;

class cached_property(object):
    """
    Decorator for cached properties.
    """
    def __init__(self, func):
        self.func = func;

        self.__name__ = func.__name__;
        self.__doc__ = func.__doc__;

    def __get__(self, obj, objType=None):
        v = self.func(obj);
        obj.__dict__[self.__name__] = v;
        return v;

class _Tokenizer(type):
    def __init__(cls, name, bases, namespace, **kwds):
        if("_tokens" not in namespace):
            return;

        r = "|".join(("(?P<%s>%s)" % t) for t in cls._tokens);
        cls._regexp = re.compile(r);

class Tokenizer(metaclass=_Tokenizer):
    """
    Tokenizer object.
    """
    def __init__(self, src):
        if(isinstance(src, str)):
            src = [src];

        self.src = iter(src);
        self.buffer = "";

    def __iter__(self):
        return self;

    def __next__(self):
        """
        Returns the next token as a tuple (type, match).
        """
        tok = None;
        while(tok is None):
            if(len(self.buffer)==0):
                self.buffer += next(self.src);
            tok = self._regexp.match(self.buffer);
            if(tok is None):
                continue;

            group, match = tok.lastgroup, tok.group(0);
            self.buffer = self.buffer[len(match):];

            # ignore whitespace
            if(group=="_"):
                tok = None;

        # each keyword is its own type
        if(group=="KEYWORD"):
            group = match;

        return (group, match);

class _Parser(type):
    class Symbol(object):
        """
        Symbol object.
        """
        def __init__(self, name, term):
            self.name = name;
            self.terminal = term;

            self.nullable = False;
            self.first = set();
            self.follow = set();
            self.last = set();

            if(term):
                self.first.add(self);
            else:
                self.last.add(self);

        def __repr__(self):
            if(self.terminal):
                return repr(self.name);

            return "<%s>" % self.name[1:];

        def __hash__(self):
            return hash(self.name);

    def _symbol(cls, name):
        """
        Returns or creates a symbol by a given [name]. Names starting with
         "#" are nonterminals.
        """
        term = (name is None) or (name[0]!="#");
        return cls.symbols.setdefault(name, cls.Symbol(name, term));

    def _first(cls, syms):
        """
        Returns the combined FIRST of a sequence of symbols [syms].
        """
        for s in syms:
            for i in s.first:
                if(i.terminal):
                    yield i;

            if(not s.nullable):
                break;

    def __init__(cls, name, bases, namespace, **kwds):
        if("_rules" not in namespace):
            return;

        cls.symbols = {};
        # convert names into Symbols
        for i, r in enumerate(cls._rules):
            cls._rules[i] = tuple(cls._symbol(s) for s in r);

        for head, *body in cls._rules:
            # determine FIRST, FOLLOW sets and nullability
            nul = True;
            prev = None;
            for sym in body:
                if(nul):
                    head.first |= sym.first;

                if(prev is not None):
                    # our FIRST may follow from last non-nullable
                    for l in prev.last:
                        l.follow |= sym.first;

                nul = nul and sym.nullable;
                prev = sym;

            head.nullable |= nul;

            # keep track of last non-nullable (for FOLLOW)
            for sym in reversed(body):
                head.last |= sym.last;

                # all these may also be followed by FOLLOW(head)
                for l in sym.last:
                    l.follow |= head.follow;

                if(not sym.nullable):
                    break;

        # generate LL(1) table
        cls.table = {};
        for rule in cls._rules:
            head, *body = rule;
            row = cls.table.setdefault(head, {});

            for col in cls._first(body):
                row[col] = rule;

            # this rule is nullable
            if(all(b.nullable for b in body)):
                for col in head.follow:
                    row[col] = rule;

        # register rule handlers
        cls._handlers = {};
        for fn in namespace.values():
            if(not hasattr(fn, "_rules")):
                continue;

            for r in fn._rules:
                cls._handlers[r] = fn;

class Parser(metaclass=_Parser):
    """
    LL(1) parser object.

    Rules must be ordered such that FIRST sets and nullability can be
     determined in one pass.
    """
    @classmethod
    def Handler(cls, *rules):
        """
        Decorator for rule handlers.
        """
        if(isinstance(rules[0], str)):
            rules = [rules];
        else:
            rules = rules[0];

        def fn(f):
            f._rules = rules;
            return f;

        return fn;

    def __init__(self, src):
        self.tokenizer = src;

    END_OF_RULE = object();

    def __iter__(self):
        """
        Parses the input and returns reductions in a "bottom-up" fashion as
         tuples (rule, matches).
        """
        stack = [self.symbols["#^"]];
        reductions = [];

        tok = next(self.tokenizer);
        sym = self.symbols[tok[0]];

        while(len(stack) > 0):
            top = stack.pop();

            # yield when fully reduced
            if(top is Parser.END_OF_RULE):
                yield reductions.pop();
                continue;

            # get next token
            if(sym==top):
                # remember matches to yield later
                reductions[-1][1].append(tok[1]);
                try:
                    tok = next(self.tokenizer);
                except StopIteration:
                    # None marks end-of-file
                    tok = None, None;

                sym = self.symbols[tok[0]];
                continue;

            elif(top.terminal):
                raise RuntimeError("expected terminal %s" % top);

            try:
                rule = self.table[top][sym];
            except KeyError:
                want = ", ".join([repr(k) for k in self.table[top].keys()]);
                got = sym;
                if(tok[0]!=tok[1]):
                    got = "%s %s" % (tok[0], repr(tok[1]));

                raise RuntimeError("unexpected %s (expect %s)" % (got, want));

            reductions.append((rule, []));

            stack.append(Parser.END_OF_RULE);
            stack.extend(reversed(rule[1:]));

    def parse(self):
        """
        Parses the input and applies handlers for each reduction.
        Returns the transformed input.
        """
        stack = [];
        for rule, match in self:
            fn = self._handlers.get(tuple(s.name for s in rule[0:2]),
                                    lambda *args: None);
            val = fn(self, stack, match);
            if(val is not None):
                stack.append(val);

        assert(len(stack)==1);
        return stack[-1];
