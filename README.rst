======
Patchy
======

.. image:: https://img.shields.io/travis/adamchainz/patchy.svg
        :target: https://travis-ci.org/adamchainz/patchy

.. image:: https://img.shields.io/pypi/v/patchy.svg
        :target: https://pypi.python.org/pypi/patchy

Patch the source of python functions at runtime.

A quick example::

    >>> def sample():
    ...    return 1
    >>> patchy.patch(sample, """
    ...     @@ -1,2 +1,2 @@
    ...      def sample():
    ...     -    return 1
    ...     +    return 2
    ... """)
    >>> sample()
    2


Why?
====

If you’re monkey-patching an external library to add some functionality, you
will probably forget to check the monkey patch when you upgrade that version.
By using a patch against its source code, you can specify some context that
you expect to remain the same in the function that will be checked before the
source is applied.

I found this with some small but important patches to Django for a project.
Since it takes a lot of energy to maintain a fork, writing monkey patches was
the quick solution, but writing actual patches is better.


How?
====

The standard library function `inspect.getsource()` is used to retrieve the
source code of the function, the patch is applied, the code is recompiled,
and the function’s code object is replaced the new one. Because nothing tends
to poke around at code objects apart from dodgy hacks like this, you don’t need
to chase any references that may exist to the function.


API
===

``replace(func, find, replace, count=None)``
--------------------------------------------

Perform a simple find and replace on source of the function ``func``’s source,
for when you don’t want to have to write a patch. ``find`` and ``replace``
should both be strings that will be passed to ``str.replace``.

If ``count`` is specified, it will be checked that exactly ``count``
occurrences of ``find`` exist, and ``ValueError`` will be raised if not.

Examples::

    >>> def sample():
    ...     return "Hi" * 5
    ...
    >>> patchy.replace("Hi", "Hello")
    >>> patchy.replace("5", "1")
    >>> sample()
    "Hello"


patch(func, patch_text)
-----------------------

Apply a patch to the source of function ``func``. ``patch_text`` will be
``textwrap.dedent()``’d and blank lines at the start and end stripped, so you
can write it inline with ``"""`` strings in your source code without breaking
your indendation levels.

If the patch is invalid, for example the context lines don’t match,
``ValueError`` will be raised.

Examples::

    >>> def sample():
    ...     return 1
    >>> patchy.patch(sample, """
    ...     @@ -2,2 +2,2 @@
    ...     -    return 1
    ...     +    return 2
    ... """)
    >>> sample()
    2
