from __future__ import absolute_import, unicode_literals, division
import attr
import io
from collections import OrderedDict
from psd_tools2.utils import read_fmt, write_fmt, trimmed_repr


class BaseElement(object):
    """
    Base element of various PSD file structs.

    If FORMAT attribute is set, read/write method automatically parse binary.
    """
    @classmethod
    def read(cls, fp):
        """Read the element from a file-like object.

        :param fp: file-like object
        """
        raise NotImplementedError()

    def write(self, fp):
        """Write the element to a file-like object.
        """
        raise NotImplementedError()

    @classmethod
    def frombytes(self, data, *args, **kwargs):
        """Read the element from bytes.

        :param data: bytes
        """
        with io.BytesIO(data) as f:
            return self.read(f, *args, **kwargs)

    def tobytes(self, *args, **kwargs):
        """Write the element to bytes.

        :rtype: bytes
        """
        with io.BytesIO() as f:
            self.write(f, *args, **kwargs)
            return f.getvalue()

    def _repr_pretty_(self, p, cycle):
        if cycle:
            return "{name}(...)".format(name=self.__class__.__name__)

        with p.group(2, '{name}('.format(name=self.__class__.__name__), ')'):
            p.breakable('')
            fields = [f for f in attr.fields(self.__class__) if f.repr]
            for idx, field in enumerate(fields):
                if idx:
                    p.text(',')
                    p.breakable()
                p.text('{field}='.format(field=field.name))
                value = getattr(self, field.name)
                if isinstance(value, bytes):
                    value = trimmed_repr(value)
                p.pretty(value)
            p.breakable('')


class ValueElement(BaseElement):
    """
    Single value element that has `value`.

    Use with `@attr.s(repr=False)` decorator.
    """
    def __repr__(self):
        return self.value.__repr__()

    def _repr_pretty_(self, p, cycle):
        if cycle:
            return self.__repr__()
        p.pretty(self.value)


class ListElement(BaseElement):
    """
    List-like element that has `items` list.

    Use with `@attr.s(repr=False)` decorator.
    """

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        for item in self.items:
            yield item

    def __getitem__(self, index):
        return self.items[index]

    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, self.items.__repr__())

    def _repr_pretty_(self, p, cycle):
        if cycle:
            return "{name}[...]".format(name=self.__class__.__name__)

        with p.group(2, '{name}['.format(name=self.__class__.__name__), ']'):
            p.breakable('')
            for idx in range(len(self.items)):
                if idx:
                    p.text(',')
                    p.breakable()
                value = self.items[idx]
                if isinstance(value, bytes):
                    value = trimmed_repr(value)
                p.pretty(value)
            p.breakable('')

    def write(self, fp, *args, **kwargs):
        return sum(item.write(fp, *args, **kwargs) for item in self)


class DictElement(BaseElement):
    """
    Dict-like element that has `items` OrderedDict.

    Use with `@attr.s(repr=False)` decorator.
    """

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        for key in self.items:
            yield key

    def __getitem__(self, key):
        return self.items[key]

    def __repr__(self):
        return '%s%s' % (self.__class__.__name__, dict.__repr__(self.items))

    def _repr_pretty_(self, p, cycle):
        if cycle:
            return "{name}[...]".format(name=self.__class__.__name__)

        with p.group(2, '{name}{{'.format(name=self.__class__.__name__), '}'):
            p.breakable('')
            for idx, key in enumerate(self.items):
                if idx:
                    p.text(',')
                    p.breakable()
                value = self.items[key]
                p.pretty(key)
                p.text(': ')
                if isinstance(value, bytes):
                    value = trimmed_repr(value)
                p.pretty(value)
            p.breakable('')

    def write(self, fp, *args, **kwargs):
        return sum(self.items[key].write(fp, *args, **kwargs) for key in self)
