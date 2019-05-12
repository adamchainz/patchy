.. :changelog:

History
-------

Pending Release
---------------

.. Insert new release notes below this line

* Drop Python 2 support, only Python 3.5+ is supported now. Python 3.4 was
  dropped as it has reached its end of life.

1.5.0 (2019-02-15)
------------------

* Support cases where the function or class name is not in the freevars. This
  allows patching ``__init__`` of a class, or patching a recursive module-level
  function.
* Support patching objects provided by dotted path string.

1.4.0 (2017-05-13)
------------------

* Added new function ``patchy.replace()``, that can be used to directly assign
  new source code to a function, without having to make a patch.

1.3.2 (2017-03-13)
------------------

* Support freevars and methods that call mangled methods.

1.3.1 (2016-05-24)
------------------

* Fixed ``setup.py`` to not fix the version of ``six`` required.
* Fixed install instruction in README.
* Added ``patchy.mc_patchface()`` as an alias for ``patchy.patch()`` because
  memes.

1.3.0 (2015-12-09)
------------------

* Remove dependency on ``pylru`` by using a simpler caching strategy

1.2.0 (2015-07-23)
------------------

* Pirate mascot!
* Patching caches the patched and unpatched versions, so unpatching and repeat
  patching/unpatching are both faster
* Patching doesn't attach an attribute to the function object any more

1.1.0 (2015-06-16)
------------------

* Fixed code compilation to use the ``__future__`` flags from the function that
  is being patched
* Added ``unpatch`` method
* Added ``temp_patch`` context manager/decorator

1.0.0 (2015-06-09)
---------------------

* First release on PyPI, featuring ``patch`` function.
