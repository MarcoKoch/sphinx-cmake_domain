sphinx-cmake_domain test
========================

Documenting variables
---------------------

.. cmake:var:: MY_VARIABLE "value"

    This is a variable.


.. cmake:var:: MY_CACHE_VARIABLE

    This is a cache variable.
    
    :type: STRING
    :default: "Hello World"


.. cmake:var:: MY_OPTION OFF

    This is a build option.
    
    :type: BOOLEAN
    :default: ON


.. cmake:var:: NOT_INDEXED
    :noindex:

    This variable should not appear on any index.
    
    :value ``WANT_ON_THE_INDEX``:
        This variable really wants on the index.
    
    :value ``SADNESS``:
        Why can't you just index it?


.. cmake:var:: NOT_LISTED_ON_INDEX
               ANOTHER_ONE_NOT_LISTED_ON_INDEX
    :noindexentry:

    This variable should be referencable but not appear on any index.


Documenting macros/functions
----------------------------

.. cmake:macro:: my_macro(<param1> <param2>)
                 my_other_macro()

    This macro does crazy things.
    
    :param <param1>:
        This is a parameter
    :arg <param2>:
        This is an other parameter


.. cmake:function:: my_function(<param1> <param2> \
                      SOURCES <source1>... \
                      [OPTIONAL] EITHER|(OR <or_value>) [THIS|THAT] \
                      [DISPLAY_NAME <name> [FINAL]])

  This function does the same, but supports much fancier arguments.


.. cmake:function:: no_args_func()

    This function has no documented arguments.


.. cmake:function:: empty_arglist_func()

    This function has an empty argument list.


.. cmake:function:: not_indexed()
    :noindex:

    This function should not appear in any index.


.. cmake:function:: not_listed_on_index()
    :noindexentry:
    
    This function should be referencable but not appear on any index.


Documenting modules
-------------------

.. cmake:module:: MyModule

  I wrote a module. This is it. I'm proud of it.


.. cmake:module:: MyOtherModule.cmake

  This is an extended module. It has an extension.


.. cmake:module:: NotIndexed
    :noindex:
    
    This module should not appear in any index.


.. cmake:module:: NotListedOnIndex
    :noindexentry:
    
    This module should be referenceable but not appear on any index.


Documenting targets
-------------------

.. cmake:target:: myapp

  Build this and be impressed.


.. cmake:target:: not-indexed
    :noindex:
    
    This target should not appear in any index.


.. cmake:target:: not-listed-on-index
    :noindexentry:
    
    This target should be referenceable but not appear on any index.


Referencing CMake entities
--------------------------

Variables
~~~~~~~~~

This links :any:`MY_VARIABLE` using ``:any:``.

This links :any:`MY_CACHE_VARIABLE` using ``:any:``.

This links :any:`MY_OPTION` using ``:any:``.

This links :any:`NOT_LISTED_ON_INDEX` using ``:any:``.

This links :any:`ANOTHER_ONE_NOT_LISTED_ON_INDEX` using ``:any:``.

This links :cmake:var:`MY_VARIABLE` using ``:cmake:var:``.

This links :cmake:var:`MY_CACHE_VARIABLE` using ``:cmake:var:``.

This links :cmake:var:`MY_OPTION` using ``:cmake:var:``.

This links :cmake:var:`NOT_LISTED_ON_INDEX` using ``:cmake:var:``.

This links :cmake:var:`ANOTHER_ONE_NOT_LISTED_ON_INDEX` using ``:cmake:var:``.


Macros/functions
~~~~~~~~~~~~~~~~

This links :any:`my_macro` using ``:any:``.

This links :any:`my_function()` with parentheses using ``:any:``.

This links :any:`no_args_func` using ``:any:``.

This links :any:`empty_arglist_func` using ``:any:``.

This links :any:`not_listed_on_index` using ``:any:``.

This links :cmake:macro:`my_macro` using ``:cmake:macro:``.

This links :cmake:macro:`my_function()` parentheses using ``:cmake:func:``.

This links :cmake:macro:`no_args_func` using ``:cmake:func:``.

This links :cmake:macro:`empty_arglist_func` using ``:cmake:func:``.

This links :cmake:macro:`not_listed_on_index` using ``:cmake:func:``.


Modules
~~~~~~~

This links :any:`MyModule` using ``:any:``.

This links :any:`MyModule.cmake` with its extension using ``:any:``

This links :any:`MyOtherModule` using ``:any:``.

This links :any:`MyOtherModule.cmake` with its extension using ``:any:``.

This links :any:`NotListedOnIndex` using ``:any:``.

This links :cmake:mod:`MyModule` using ``:cmake:mod:``.

This links :cmake:mod:`MyModule.cmake` with its extension using ``:cmake:mod:``

This links :cmake:mod:`MyOtherModule` using ``:cmake:mod:``.

This links :cmake:mod:`MyOtherModule.cmake` with its extension
using ``:cmake:mod:``.

This links :cmake:mod:`NotListedOnIndex` using ``:cmake:mod:``.


Targets
~~~~~~~

This links :any:`myapp` using ``:any:``.

This links :any:`not-listed-on-index` using ``:any:``.

This links :cmake:tgt:`myapp` using ``:cmake:tgt:``.

This links :cmake:tgt:`not-listed-on-index` using ``:cmake:tgt:``.


Indices
-------

* :ref:`genindex`
* :ref:`cmake-index`
