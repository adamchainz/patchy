=========
Changelog
=========

2.10.0 (2025-09-09)
-------------------

* Support Python 3.14.

2.9.0 (2024-10-25)
------------------

* Drop Python 3.8 support.

* Support Python 3.13.

2.8.0 (2023-07-10)
------------------

* Drop Python 3.7 support.

2.7.0 (2023-06-16)
------------------

* Support Python 3.12.

2.6.1 (2023-01-16)
------------------

* Use the ``--force`` flag to ``patch``, so it doesn’t hang waiting input for invalid reverse patches.
  This seems to happen with the new version on macOS.

2.6.0 (2022-05-11)
------------------

* Support Python 3.11.

2.5.0 (2022-01-10)
------------------

* Drop Python 3.6 support.

2.4.0 (2021-08-11)
------------------

* Add type hints.

2.3.0 (2021-05-10)
------------------

* Support Python 3.10.

* Stop distributing tests to reduce package size. Tests are not intended to be
  run outside of the tox setup in the repository. Repackagers can use GitHub's
  tarballs per tag.

2.2.0 (2020-12-13)
------------------

* Drop Python 3.5 support.
* Move license from BSD to MIT License.

2.1.0 (2020-02-20)
------------------

* Support Python 3.9.
* Use Python 3.9's ``pkgutil.resolve_name()``
  (`docs <https://docs.python.org/3.9/library/pkgutil.html#pkgutil.resolve_name>`__)
  to import names by strings, and depend on the
  `backport package <https://pypi.org/project/pkgutil_resolve_name/>`__ on
  older Python versions.

2.0.0 (2019-11-15)
------------------

* Drop Python 2 support, only Python 3.5-3.8 is supported now. Python 3.4 was
  dropped as it has reached its end of life.
* Converted setuptools metadata to configuration file. This meant removing the
  ``__version__`` attribute from the package. If you want to inspect the
  installed version, use
  ``importlib.metadata.version("patchy")``
  (`docs <https://docs.python.org/3.8/library/importlib.metadata.html#distribution-versions>`__ /
  `backport <https://pypi.org/project/importlib-metadata/>`__).

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
