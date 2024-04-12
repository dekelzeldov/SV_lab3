import collections.abc;

# Blom, S.; Lisser, B.; Van de Pol, J. et al. "A Database Approach to
# Distributed State Space Generation". Electronic Notes in Theoretical Computer
# Science, vol. 198, issue 1 (2008): 17--32.

class TreeSet(collections.abc.MutableSet):
    """
    Tree-based state set object.
    """
    def __init__(self):
        self.data = [];
        self.out = [None, None];

    def __len__(self):
        return sum(1 for _ in iter(self));

    def _get(self, pair):
        """
        Returns the full tuple for a given [pair].
        """
        out, lo = self.out[0], pair[0];
        if(out is not None):
            lo = out._get(out.data[lo]);
        else:
            lo = (lo,);

        out, hi = self.out[1], pair[1];
        if(out is not None):
            hi = out._get(out.data[hi]);
        else:
            hi = (hi,);

        return lo + hi;

    def __iter__(self):
        for pair in self.data:
            yield self._get(pair);

    def _split(self, item):
        """
        Splits a given tuple [item].
        """
        if(self.out[0] is None):
            return item[0], item[1:];
        if(self.out[1] is None):
            return item[:-1], item[-1];

        l = (len(item) + 1) // 2;
        return item[:l], item[l:];

    def _index(self, item):
        """
        Returns the index a given tuple [item] can be found at.
        """
        if(self.out[0] is None and self.out[1] is None):
            return self.data.index(item);

        lo, hi = self._split(item);
        if(self.out[0] is not None):
            lo = self.out[0]._index(lo);
        if(self.out[1] is not None):
            hi = self.out[1]._index(hi);

        return self.data.index((lo, hi));

    def __contains__(self, item):
        item = tuple(item);
        try:
            i = self._index(item);
            return True;
        except ValueError as e:
            return False;

    def _add(self, item):
        """
        Add a given tuple [item] to this set.
        """
        l = (len(item) + 1) // 2;
        lo, hi = item[:l], item[l:];

        if(len(lo) > 1):
            if(self.out[0] is None):
                self.out[0] = TreeSet();
            lo = self.out[0]._add(lo);
        else:
            lo = lo[0];

        if(len(hi) > 1):
            if(self.out[1] is None):
                self.out[1] = TreeSet();
            hi = self.out[1]._add(hi);
        else:
            hi = hi[0];

        pair = (lo, hi);
        try:
            n = self.data.index(pair);
        except ValueError:
            n = len(self.data);
            self.data.append(pair);

        return n;

    def add(self, item):
        """
        Add a given state [item] to this set.
        """
        self._add(tuple(item));

    def discard(self, item):
        """
        Remove a given state [item] from this set.
        """
        raise NotImplementedError;
