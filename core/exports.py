# Export some functions to be dynamically called by the core module to avoid circular imports...
# Only use them when resolving circular import hell...

Silian_exports = {}


def add_export(func, name=None):
    Silian_exports[func.__name__ if not name else name] = func
