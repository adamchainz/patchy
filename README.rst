======
Patchy
======

.. image:: https://img.shields.io/travis/adamchainz/patchy/master.svg
        :target: https://travis-ci.org/adamchainz/patchy

.. image:: https://img.shields.io/pypi/v/patchy.svg
        :target: https://pypi.python.org/pypi/patchy

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/python/black

.. figure:: https://raw.github.com/adamchainz/patchy/master/pirate.png
   :alt: A patchy pirate.

..

Patch the inner source of python functions at runtime.

A quick example, making a function that returns 1 instead return 9001:

.. code-block:: python

    >>> def sample():
    ...    return 1
    >>> patchy.patch(sample, """\
    ...     @@ -1,2 +1,2 @@
    ...      def sample():
    ...     -    return 1
    ...     +    return 9001
    ...     """)
    >>> sample()
    9001

Patchy works by replacing the code attribute of the function, leaving the
function object itself the same. It's thus more versatile than monkey patching,
since if the function has been imported in multiple places they'll also call
the new behaviour.


Installation
============

Use **pip**:

.. code-block:: bash

    pip install patchy

Requirements
============

Tested with all combinations of:

* Python: 3.5, 3.6, 3.7

Python 3.5+ supported.

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
* At least with monkey-patching you know what end up with, rather than having
  the changes being done at runtime to source that may have changed.

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

A little special treatment is given to ``instancemethod``, ``classmethod``, and
``staticmethod`` objects to make sure the underlying function is what gets
patched and that you don't have to worry about the details.


API
===

``patch(func, patch_text)``
---------------------------

Apply the patch ``patch_text`` to the source of function ``func``. ``func`` may
be either a function, or a string providing the dotted path to import a
function.

If the patch is invalid, for example the context lines don’t match,
``ValueError`` will be raised, with a message that includes all the output from
the ``patch`` utility.

Note that ``patch_text`` will be ``textwrap.dedent()``’ed, but leading
whitespace will not be removed. Therefore the correct way to include the patch
is with a triple-quoted string with a backslash - ``"""\`` - which starts the
string and avoids including the first newline. A final newline is not required
and will be automatically added if not present.

Example:

.. code-block:: python

    import patchy

    def sample():
        return 1

    patchy.patch(sample, """\
        @@ -2,2 +2,2 @@
        -    return 1
        +    return 2""")

    print(sample())  # prints 2


``mc_patchface(func, patch_text)``
----------------------------------

An alias for ``patch``, so you can meme it up by calling
``patchy.mc_patchface()``.


``unpatch(func, patch_text)``
-----------------------------

Unapply the patch ``patch_text`` from the source of function ``func``. This is
the reverse of ``patch()``\ing it, and calls ``patch --reverse``.

The same error and formatting rules apply as in ``patch()``.

Example:

.. code-block:: python

    import patchy

    def sample():
        return 2

    patchy.unpatch(sample, """\
        @@ -2,2 +2,2 @@
        -    return 1
        +    return 2""")

    print(sample())  # prints 1


``temp_patch(func, patch_text)``
--------------------------------

Takes the same arguments as ``patch``. Usable as a context manager or function
decorator to wrap code with a call to ``patch`` before and ``unpatch`` after.

Context manager example:

.. code-block:: python

    def sample():
        return 1234

    patch_text = """\
        @@ -1,2 +1,2 @@
         def sample():
        -    return 1234
        +    return 5678
        """

    with patchy.temp_patch(sample, patch_text):
        print(sample())  # prints 5678

Decorator example, using the same ``sample`` and ``patch_text``:

.. code-block:: python

    @patchy.temp_patch(sample, patch_text)
    def my_func():
        return sample() == 5678

    print(my_func())  # prints True


``replace(func, expected_source, new_source)``
----------------------------------------------

Check that function or dotted path to function ``func`` has an AST matching
`expected_source``, then replace its inner code object with source compiled
from ``new_source``. If the AST check fails, ``ValueError`` will be raised with
current/expected source code in the message. In the author's opinion it's
preferable to call ``patch()`` so your call makes it clear to see what is being
changed about ``func``, but using ``replace()`` is simpler as you don't have to
make a patch and there is no subprocess call to the ``patch`` utility.

Note both ``expected_source`` and ``new_source`` will be
``textwrap.dedent()``’ed, so the best way to include their source is with a
triple quoted string with a backslash escape on the first line, as per the
example below.

If you want, you can pass ``expected_source=None`` to avoid the guard against
your target changing, but this is highly unrecommended as it means if the
original function changes, the call to ``replace()`` will continue to silently
succeed.

Example:

.. code-block:: python

    import patchy

    def sample():
        return 1

    patchy.replace(
        sample,
        """\
        def sample():
            return 1
        """,
        """\
        def sample():
            return 42
        """
    )

    print(sample())  # prints 42


How to Create a Patch
=====================

1. Save the source of the function of interest (and nothing else) in a ``.py``
   file, e.g. ``before.py``:

   .. code-block:: python

       def foo():
           print("Change me")

   Make sure you dedent it so there is no whitespace before the ``def``, i.e.
   ``d`` is the first character in the file. For example if you wanted to patch
   the ``bar()`` method below:

   .. code-block:: python

       class Foo():
           def bar(self, x):
               return x * 2

   ...you would put just the method in a file like so:

   .. code-block:: python

       def bar(self, x):
           return x * 2

   However we'll continue with the first example ``before.py`` since it's
   simpler.

2. Copy that ``.py`` file, to e.g. ``after.py``, and make the changes you
   want, such as:

   .. code-block:: python

       def foo():
           print("Changed")

3. Run ``diff``, e.g. ``diff before.py after.py``. You will get output like:

   .. code-block:: diff

      diff --git a/Users/chainz/tmp/before.py b/Users/chainz/tmp/after.py
      index e6b32c6..31fe8d9 100644
      --- a/Users/chainz/tmp/before.py
      +++ b/Users/chainz/tmp/after.py
      @@ -1,2 +1,2 @@
       def foo():
      -    print("Change me")
      +    print("Changed")

4. The filenames are not necessary for ``patchy`` to work. Take only from the
   first ``@@`` line onwards into the multiline string you pass to
   ``patchy.patch()``:

   .. code-block:: python

      patchy.patch(foo, """\
          @@ -1,2 +1,2 @@
           def foo():
          -    print("Change me")
          +    print("Changed")
          """)
