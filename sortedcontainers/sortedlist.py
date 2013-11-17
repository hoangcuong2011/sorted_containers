"""
Sorted list implementation.
"""

from bisect import bisect_left, bisect_right, insort
from itertools import chain, izip, imap
from collections import MutableSequence
from operator import iadd

class SortedList(MutableSequence):
    def __init__(self, iterable=None, load=100):
        self.clear()
        self._load, self._twice, self._half = load, load * 2, load / 2

        if iterable is not None:
            self.update(iterable)

    def clear(self):
        self._len, self._maxes, self._lists, self._index = 0, None, [], []

    def add(self, val):
        """Add a val to the sorted list."""
        if self._maxes is None:
            self._maxes = [val]
            self._lists = [[val]]
        else:
            pos = bisect_right(self._maxes, val)

            if pos == len(self._maxes):
                pos -= 1
                self._maxes[pos] = val
                self._lists[pos].append(val)
            else:
                insort(self._lists[pos], val)

            del self._index[pos:]
            self._expand(pos)

        self._len += 1

    def _expand(self, pos):
        if len(self._lists[pos]) > self._twice:
            half = self._lists[pos][self._load:]
            self._lists[pos] = self._lists[pos][:self._load]
            self._maxes[pos] = self._lists[pos][-1]
            self._maxes.insert(pos + 1, half[-1])
            self._lists.insert(pos + 1, half)
            del self._index[pos:]

    def update(self, iterable):
        """Update this sorted list with values from iterable."""
        values = sorted(iterable)

        if self._maxes is None and len(values) > 0:
            self._lists = [values[pos:(pos + self._load)]
                          for pos in xrange(0, len(values), self._load)]
            self._maxes = [sublist[-1] for sublist in self._lists]
            self._len = len(values)
            del self._index[:]
        else:
            for val in values:
                self.add(val)

    def __contains__(self, val):
        """Return True iff val in sorted list."""
        if self._maxes is None:
            return False

        pos = bisect_left(self._maxes, val)

        if pos == len(self._maxes):
            return False

        idx = bisect_left(self._lists[pos], val)

        return self._lists[pos][idx] == val

    def discard(self, val):
        """Remove the first occurrence of val.
        If val is not a member, does nothing."""
        if self._maxes is None:
            return

        pos = bisect_left(self._maxes, val)

        if pos == len(self._maxes):
            return

        idx = bisect_left(self._lists[pos], val)

        if self._lists[pos][idx] == val:
            self._delete(pos, idx)

    def remove(self, val):
        """Remove the first occurrence of val.
        If val is not a member, raise ValueError."""
        if self._maxes is None:
            raise ValueError

        pos = bisect_left(self._maxes, val)

        if pos == len(self._maxes):
            raise ValueError

        idx = bisect_left(self._lists[pos], val)

        if self._lists[pos][idx] == val:
            self._delete(pos, idx)
        else:
            raise ValueError

    def _delete(self, pos, idx):
        """Delete the item at the given (pos, idx).
        Combines lists that are less than half the load level."""
        del self._lists[pos][idx]
        self._len -= 1
        del self._index[pos:]

        if len(self._lists[pos]) == 0:
            del self._maxes[pos]
            del self._lists[pos]

            if len(self._maxes) == 0:
                self._maxes = None
                self._lists = []
        else:
            self._maxes[pos] = self._lists[pos][-1]

            if len(self._lists) > 1 and len(self._lists[pos]) < self._half:
                if pos == 0: pos += 1
                prev = pos - 1
                self._lists[prev].extend(self._lists[pos])
                self._maxes[prev] = self._lists[prev][-1]
                del self._maxes[pos]
                del self._lists[pos]
                del self._index[prev:]
                self._expand(prev)

    def _loc(self, pos, idx):
        if pos == 0:
            return idx

        end = len(self._index)

        if pos >= end:

            repeat = pos - end + 1
            prev = self._index[-1] if end > 0 else 0

            for rpt in xrange(repeat):
                next = prev + len(self._lists[end + rpt])
                self._index.append(next)
                prev = next

        return self._index[pos - 1] + idx

    def _pos(self, idx):
        if self._maxes is None:
            raise IndexError

        if idx < 0:
            idx += self._len
        if idx < 0:
            raise IndexError
        if idx >= self._len:
            raise IndexError

        pos = bisect_right(self._index, idx)

        if pos == len(self._index):
            prev = self._index[-1] if pos > 0 else 0

            while prev <= idx:
                next = prev + len(self._lists[pos])
                self._index.append(next)
                prev = next
                pos += 1

            pos -= 1

        if pos == 0:
            return (pos, idx)
        else:
            return (pos, (idx - self._index[pos - 1]))

    def __delitem__(self, idx):
        if isinstance(idx, slice):
            raise NotImplementedError
        else:
            pos, idx = self._pos(idx)
            self._delete(pos, idx)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            raise NotImplementedError
        else:
            pos, idx = self._pos(idx)
            return self._lists[pos][idx]

    def __setitem__(self, idx, val):
        if isinstance(idx, slice):
            raise NotImplementedError
        else:
            pos, loc = self._pos(idx)

            if idx < 0: idx += self._len

            # Check that the inserted value is not less than the
            # previous value.

            if idx > 0:
                idx_prev = loc - 1
                pos_prev = pos

                if idx_prev < 0:
                    pos_prev -= 1
                    idx_prev = len(self._lists[pos_prev]) - 1

                if self._lists[pos_prev][idx_prev] > val:
                    raise ValueError

            # Check that the inserted value is not greater than
            # the previous value.

            if idx < (self._len - 1):
                idx_next = loc + 1
                pos_next = pos

                if idx_next == len(self._lists[pos_next]):
                    pos_next += 1
                    idx_next = 0

                if self._lists[pos_next][idx_next] < val:
                    raise ValueError

            self._lists[pos][loc] = val

    def __iter__(self):
        return chain.from_iterable(self._lists)

    def reversed(self):
        start = len(self._lists) - 1
        iterable = (reversed(self._lists[pos])
                    for pos in xrange(start, -1, -1))
        return chain.from_iterable(iterable)

    def __len__(self):
        return self._len

    def bisect_left(self, val):
        if self._maxes is None:
            return 0

        pos = bisect_left(self._maxes, val)

        if pos == len(self._maxes):
            return self._len

        idx = bisect_left(self._lists[pos], val)

        return self._loc(pos, idx)

    def bisect(self, val):
        return self.bisect_left(val)

    def bisect_right(self, val):
        if self._maxes is None:
            return 0

        pos = bisect_right(self._maxes, val)

        if pos == len(self._maxes):
            return self._len

        idx = bisect_right(self._lists[pos], val)

        return self._loc(pos, idx)

    def count(self, val):
        if self._maxes is None:
            return 0

        left = self.bisect_left(val)
        right = self.bisect_right(val)

        return right - left

    def append(self, val):
        """Append the given val to the end of the sorted list.
        Raises ValueError if the val would make the list unsorted.
        """
        if self._maxes is None:
            self._maxes = [val]
            self._lists = [[val]]
            self._len = 1
            return

        pos = len(self._lists) - 1

        if val < self._lists[pos][-1]:
            raise ValueError

        self._maxes[pos] = val
        self._lists[pos].append(val)
        self._len += 1
        del self._index[pos:]

        self._expand(pos)

    def extend(self, values):
        """Extend this list with the given values.
        Raises ValueError if the values would make the list unsorted.
        """
        if not isinstance(values, list):
            values = list(values)

        if any(values[pos - 1] > values[pos]
               for pos in xrange(1, len(values))):
            raise ValueError

        offset = 0
        count = len(self._lists) - 1

        if self._maxes is None:
            self._maxes = []
            self._lists = []
        else:
            if values[0] < self._lists[-1][-1]:
                raise ValueError

            if len(self._lists[-1]) < self._half:
                self._lists[-1].extend(values[:self._load])
                self._maxes[-1] = self._lists[-1][-1]
                offset = self._load

        for idx in xrange(offset, len(values), self._load):
            self._lists.append(values[idx:(idx + self._load)])
            self._maxes.append(self._lists[-1][-1])

        self._len += len(values)
        del self._index[count:]

    def insert(self, idx, val):
        """Insert the given val at idx.
        Raise ValueError if the val at idx would make the list unsorted.
        """
        if idx < 0:
            idx += self._len
        if idx < 0:
            idx = 0
        if idx > self._len:
            idx = self._len

        if self._maxes is None:
            # The idx must be zero by the inequalities above.
            self._maxes = [val]
            self._lists = [[val]]
            self._len = 1
            return

        if idx == 0:
            if val > self._lists[0][0]:
                raise ValueError
            else:
                self._lists[0].insert(0, val)
                self._expand(0)
                self._len += 1
                del self._index[:]
                return

        if idx == self._len:
            pos = len(self._lists) - 1
            if self._lists[pos][-1] > val:
                raise ValueError
            else:
                self._lists[pos].append(val)
                self._maxes[pos] = self._lists[pos][-1]
                self._expand(pos)
                self._len += 1
                del self._index[pos:]
                return

        pos, idx = self._pos(idx)
        idx_before = idx - 1
        if idx_before < 0:
            pos_before = pos - 1
            idx_before = len(self._lists[pos_before]) - 1
        else:
            pos_before = pos

        before = self._lists[pos_before][idx_before]
        if before <= val <= self._lists[pos][idx]:
            self._lists[pos].insert(idx, val)
            self._expand(pos)
            self._len += 1
            del self._index[pos:]
        else:
            raise ValueError

    def pop(self, idx=-1):
        if idx < 0:
            idx += self._len
        if idx < 0 or idx >= self._len:
            raise IndexError

        pos, idx = self._pos(idx)
        val = self._lists[pos][idx]
        self._delete(pos, idx)

        return val

    def index(self, val, start=None, stop=None):
        if self._maxes is None:
            raise ValueError

        if start == None:
            start = 0
        if start < 0:
            start += self._len
        if start < 0:
            start = 0

        if stop == None:
            stop = self._len
        if stop < 0:
            stop += self._len
        if stop > self._len:
            stop = self._len

        if stop <= start:
            raise ValueError

        stop -= 1

        left = self.bisect_left(val)

        if (left == self._len) or (self[left] != val):
            raise ValueError

        right = self.bisect_right(val) - 1

        pos = max(start, left)

        if pos <= right and pos <= stop:
            return pos

        raise ValueError

    def as_list(self):
        return reduce(iadd, self._lists, [])

    def __add__(self, that):
        values = self.as_list()
        values.extend(that)
        return SortedList(values)

    def __iadd__(self, that):
        self.update(that)
        return self

    def __mul__(self, that):
        values = self.as_list() * that
        return SortedList(values)

    def __imul__(self, that):
        values = self.as_list() * that
        self.clear()
        self.update(values)
        return self

    def __eq__(self, that):
        return ((self._len == len(that))
                and all(lhs == rhs for lhs, rhs in izip(self, that)))

    def __ne__(self, that):
        return ((self._len != len(that))
                or any(lhs != rhs for lhs, rhs in izip(self, that)))

    def __lt__(self, that):
        return ((self._len <= len(that))
                and all(lhs < rhs for lhs, rhs in izip(self, that)))

    def __le__(self, that):
        return ((self._len <= len(that))
                and all(lhs <= rhs for lhs, rhs in izip(self, that)))

    def __gt__(self, that):
        return ((self._len >= len(that))
                and all(lhs > rhs for lhs, rhs in izip(self, that)))

    def __ge__(self, that):
        return ((self._len >= len(that))
                and all(lhs >= rhs for lhs, rhs in izip(self, that)))

    def __repr__(self):
        reprs = (repr(value) for value in self)
        return 'SortedList([{}])'.format(', '.join(reprs))

    def _check(self):
        try:
            # Check load parameters.

            assert self._load >= 4
            assert self._half == (self._load / 2)
            assert self._twice == (self._load * 2)

            # Check empty sorted list case.

            if self._maxes is None:
                assert self._lists == []
                return

            assert len(self._maxes) > 0 and len(self._lists) > 0

            # Check all sublists are sorted.

            assert all(sublist[pos - 1] <= sublist[pos]
                       for sublist in self._lists
                       for pos in xrange(1, len(sublist)))

            # Check beginning/end of sublists are sorted.

            for pos in xrange(1, len(self._lists)):
                assert self._lists[pos - 1][-1] <= self._lists[pos][0]

            # Check length of _maxes and _lists match.

            assert len(self._maxes) == len(self._lists)

            # Check _maxes is a map of _lists.

            assert all(self._maxes[pos] == self._lists[pos][-1]
                       for pos in xrange(len(self._maxes)))

            # Check load level is less than _twice.

            assert all(len(sublist) <= self._twice for sublist in self._lists)

            # Check load level is greater than _half for all
            # but the last sublist.

            assert all(len(self._lists[pos]) >= self._half
                       for pos in xrange(0, len(self._lists) - 1))

            # Check length.

            assert self._len == sum(len(sublist) for sublist in self._lists)

            # Check cumulative sum cache.

            cumulative_sum_len = [len(self._lists[0])]
            for pos in xrange(1, len(self._index)):
                cumulative_sum_len.append(cumulative_sum_len[-1] + len(self._lists[pos]))
            assert all((self._index[pos] == cumulative_sum_len[pos])
                       for pos in xrange(len(self._index)))

        except AssertionError:
            import sys, traceback

            traceback.print_exc(file=sys.stdout)

            print self._len, self._load, self._half, self._twice
            print self._index
            print self._maxes
            print self._lists

            raise
