"""Utility module."""

from importlib import import_module


def import_string(dotted_path):
    """
    Imports a class from the its full path.
    :param dotted_path: The path to be imported.
    """

    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        raise LookupError(msg)

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (dotted_path, class_name)
        raise LookupError(msg)
