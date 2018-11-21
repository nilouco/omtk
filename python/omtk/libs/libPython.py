import gc
import imp
import inspect
import itertools
import logging
import re
import sys
import threading

log = logging.getLogger(__name__)

_g_regex_prefix = re.compile('(.*[^0-9]+)([0-9]*)$')

if False:  # for type hinting
    from typing import List, Set, Dict, Tuple


def does_module_exist(module_name):
    try:
        imp.find_module(module_name)
        return True
    except ImportError:
        return False


# src: http://code.activestate.com/recipes/66472/
def frange(start, end=None, inc=None):
    "A range function, that does accept float increments..."

    if end is None:
        end = start + 0.0
        start = 0.0

    if inc is None:
        inc = 1.0

    L = []
    while 1:
        next = start + len(L) * inc
        if inc > 0 and next >= end:
            break
        elif inc < 0 and next <= end:
            break
        L.append(next)

    return L


def resize_list(val, desired_size, default=None):
    list_size = len(val)
    if list_size > desired_size:
        for i in range(list_size - desired_size):
            val.pop(-1)
    elif list_size < desired_size:
        for i in range(desired_size - list_size):
            val.append(default)


#
# Taken from libSerialization
#


def get_class_namespace(classe, relative=False):
    if not isinstance(classe, object):
        return None  # Todo: throw exception
    class_name = classe.__name__
    if relative:
        tokens = class_name.split('.')
        return tokens[-1] if tokens else None
    else:
        tokens = []
        while classe is not object:
            tokens.append(class_name)
            classe = classe.__bases__[0]
        return '.'.join(reversed(tokens))


def get_class_def(class_name, base_class=object, relative=False):
    try:
        for cls in base_class.__subclasses__():
            cls_path = get_class_namespace(cls, relative=relative)
            if cls_path == class_name:
                return cls
            else:
                t = get_class_def(class_name, base_class=cls, relative=relative)
                if t is not None:
                    return t
    except Exception as e:
        pass
        # log.warning("Error obtaining class definition for {0}: {1}".format(class_name, e))
    return None


def create_class_instance(class_name):
    cls = get_class_def(class_name)

    if cls is None:
        log.warning("Can't find class definition '{0}'".format(class_name))
        return None

    class_def = getattr(sys.modules[cls.__module__], cls.__name__)
    assert (class_def is not None)

    try:
        return class_def()
    except Exception as e:
        log.error("Fatal error creating '{0}' instance: {1}".format(class_name, str(e)))
        return None


def get_sub_classes(_cls):
    for subcls in _cls.__subclasses__():
        yield subcls
        for subsubcls in get_sub_classes(subcls):
            yield subsubcls


class LazySingleton(object):
    """A threadsafe singleton that initialises when first referenced."""

    def __init__(self, instance_class, *nargs, **kwargs):
        self.instance_class = instance_class
        self.nargs = nargs
        self.kwargs = kwargs
        self.lock = threading.Lock()
        self.instance = None

    def __call__(self):
        if self.instance is None:
            try:
                self.lock.acquire()
                if self.instance is None:
                    self.instance = self.instance_class(*self.nargs, **self.kwargs)
                    self.nargs = None
                    self.kwargs = None
            finally:
                self.lock.release()
        return self.instance


def get_class_parent_level(cls, level=0):
    """
    Return the highest number of sub-classes before reaching the object case class.
    """
    next_level = level + 1
    levels = [get_class_parent_level(base_cls, level=next_level) for base_cls in cls.__bases__]
    if levels:
        return max(levels)
    else:
        return level


def objects_by_id(id_):
    for obj in gc.get_objects():
        if id(obj) == id_:
            return obj
    raise Exception("No found")


# src: https://docs.python.org/2/library/itertools.html
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


# -- Algorithms --

# http://eddmann.com/posts/depth-first-search-and-breadth-first-search-in-python/
def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    visited.add(start)
    for next in graph[start] - visited:
        dfs(graph, next, visited)
    return visited


# http://eddmann.com/posts/using-iterative-deepening-depth-first-search-in-python/
def id_dfs(puzzle, goal, get_moves, max_iteration=20, known=None):
    """
    :param puzzle:
    :param goal:
    :param get_moves:
    :param max_iteration:
    :param known: A set that will keep track of explored nodes. Created if not provided.
    :return:
    """
    import itertools
    if known is None:
        known = set()

    def dfs(route, depth):
        if depth == 0:
            return
        if goal(route[-1]):
            return route
        for move in get_moves(route[-1]):
            if move not in route and move not in known:
                known.add(move)
                next_route = dfs(route + [move], depth - 1)
                if next_route:
                    return next_route

    for depth in itertools.count(start=1):
        if max_iteration and depth > max_iteration:
            raise StopIteration("Maximum iteration limit!")
        known.clear()
        route = dfs([puzzle], depth)
        if route:
            return route


def get_unique_key(name, all_names, naming_format='{0}{1}', start=1):
    """

    >>> get_unique_key('v1', ['v1', 'v2'])
    'v3'
    >>> get_unique_key('v', ['v', 'v1', 'v2'])
    'v3'

    :param name:
    :type name: str
    :param all_names:
    :type all_names: List[str] or Tuple[str] or Set[str] or Dict[str]
    :param naming_format:
    :param enforce_suffix:
    :param start:
    :return:
    """
    if not name in all_names:
        return name

    name, prefix = _g_regex_prefix.match(name).groups()
    if prefix:
        start = int(prefix) + 1  # we'll try next

    for i in itertools.count(start):
        new_name = naming_format.format(name, i)
        if new_name not in all_names:
            return new_name


def rreload(module):
    """
    Recursive reload function.
    :param module:
    """
    _known = {type, object, None}
    namespace = module.__name__

    def _reload(m):
        # print "scanning ", m
        if m in _known:
            return
        _known.add(m)

        # child?
        m_name = m.__name__
        if not m_name.startswith(namespace):
            return

        if m_name in sys.builtin_module_names:
            return

        # print "accepted", m
        for name, value in inspect.getmembers(m):
            # Reload class
            if inspect.isclass(value):
                cls_module = inspect.getmodule(value)
                if cls_module:
                    if not cls_module.__name__.startswith(namespace):
                        continue
                    _reload(cls_module)  # if reload occured
                    # print "Successfully reloaded {}, will update {}".format(cls_module.__name__, name)
                    # Update local class pointer
                    try:
                        cls_name = getattr(cls_module, value.__name__)
                    except AttributeError as e:
                        print("{}.{} error: {}".format(cls_module.__name__, value.__name__, e))
                        continue

                    # print "set {}.{} to {} ({}.{})".format(m_name, name, cls_name, cls_module.__name__, name)
                    setattr(m, name, cls_name)

            # Reload function
            if inspect.isfunction(value):
                fn_module = inspect.getmodule(value)
                if fn_module:
                    if not fn_module.__name__.startswith(namespace):
                        continue
                    _reload(fn_module)
                    try:
                        cls_name = getattr(fn_module, value.__name__)
                    except AttributeError as e:
                        print("{}.{} error: {}".format(fn_module.__name__, value.__name__, e))
                        continue

                    # print "set {}.{} to {} ({}.{})".format(m_name, name, cls_name, fn_module.__name__, name)
                    setattr(m, name, cls_name)

            if inspect.ismodule(value):
                _reload(value)

        print "Reloading %s" % m_name
        reload(module)

        return True

    print namespace
    _reload(module)
