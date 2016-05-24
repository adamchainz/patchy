.. :changelog:

History
-------

Pending Release
---------------


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
