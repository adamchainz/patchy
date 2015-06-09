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
    >>> patchy.patch(sample, """\
    ...     @@ -2,2 +2,2 @@
    ...     -    return 1
    ...     +    return 9001""")
    >>> sample()
    9001


Why?
====

If you’re monkey-patching an external library to add or fix some functionality,
you will probably forget to check the monkey patch when you upgrade it. By
using a patch against its source code, you can specify some context that you
expect to remain the same in the function that will be checked before the
source is applied.

I found this with some small but important patches to Django for a project.
Since it takes a lot of energy to maintain a fork, writing monkey patches was
the chosen quick solution, but then writing actual patches would be better.

The patches are applied with the standard ``patch`` commandline utility.


Why not?
========

There are of course a lot of reasons against:

* It’s (relatively) slow (since it writes the source to disk and calls the
  ``patch`` command)
* If you have a patch file, why not just fork the library and apply it?
* At least with monkey-patching you know you end up with, rather than having a
  the changes being done at runtime

All are valid arguments. However once in a while this might be the right
solution.


How?
====

The standard library function ``inspect.getsource()`` is used to retrieve the
source code of the function, the patch is applied with the commandline utility
``patch``, the code is recompiled, and the function’s code object is replaced
the new one. Because nothing tends to poke around at code objects apart from
dodgy hacks like this, you don’t need to worry about chasing any references
that may exist to the function, unlike ``mock.patch``.


API
===

``replace(func, find, replace, count=None)``
--------------------------------------------

Perform a simple find and replace on source of the function ``func``’s source -
for when you don’t want to have to write a patch. ``find`` and ``replace``
should both be strings that will be passed to ``str.replace``.

If ``count`` is specified, it will be checked that exactly ``count``
occurrences of ``find`` exist, and ``ValueError`` will be raised if not.

Example::

    >>> def sample():
    ...     return "Hi" * 5
    ...
    >>> patchy.replace("Hi", "Hello")
    >>> patchy.replace("5", "1")
    >>> sample()
    "Hello"


``patch(func, patch_text)``
---------------------------

Apply the patch ``patch_text`` to the source of function ``func``.

If the patch is invalid, for example the context lines don’t match,
``ValueError`` will be raised, with a message that includes all the output from
the ``patch`` utility.

Note that ``patch_text`` will be ``textwrap.dedent()``’ed, but leading
whitespace will not be removed. Therefore the correct way to include the patch
is with a triple-quoted string with a backslash - ``"""\`` - which starts the
string and avoids including the first newline. A final newline is not required
and will be automatically added if not present.

Example::

    >>> def sample():
    ...     return 1
    >>> patchy.patch(sample, """\
    ...     @@ -2,2 +2,2 @@
    ...     -    return 1
    ...     +    return 2""")
    >>> sample()
    2


How to Create a Patch
=====================

1. Save the source of the function of interest in a ``.py`` file, e.g.
   ``before.py``. Make sure you dedent it so there is no whitespace before the
   ``def``::

       def foo():
           print("Change me")

2. Copy that ``.py`` file, to e.g. ``after.py``, and make the changes you
   want::

       def foo():
           print("Changed")

3. Run ``diff``, e.g. ``diff before.py after.py``. You will get output like::

      diff --git a/Users/chainz/tmp/before.py b/Users/chainz/tmp/after.py
      index e6b32c6..31fe8d9 100644
      --- a/Users/chainz/tmp/before.py
      +++ b/Users/chainz/tmp/after.py
      @@ -1,2 +1,2 @@
       def foo():
      -    print("Change me")
      +    print("Changed")

4. The filenames are not necessary for patchy to work. Take only from the first
   ``@@`` line onwards into the multiline string you pass to
   ``patchy.patch()``::

      patchy.patch(foo, """\
          @@ -1,2 +1,2 @@
           def foo():
          -    print("Change me")
          +    print("Changed")
          """)
