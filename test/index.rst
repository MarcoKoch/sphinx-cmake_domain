sphinx-cmake_domain test
========================

Documenting variables
---------------------

.. cmake:var:: MY_VARIABLE

    This is a variable.


.. cmake:var:: MY_CACHE_VARIABLE

    This is a cache variable.
    
    :type: STRING
    :default: "Hello World"


.. cmake:var:: MY_OPTION

    This is a build option.
    
    :type: BOOLEAN
    :default: ON


.. cmake:var:: MY_OPTION

    This is a second definition of the same option.


.. cmake:var:: NOT_INDEXED
    :noindex:

    This variable should not appear in any index.


.. cmake:var:: NOT_LISTED_ON_INDEX
               ANOTHER_ONE_NOT_LISTED_ON_INDEX
    :noindexentry:

    This variable should be referencable but not appear in any index.


Documenting macros/functions
----------------------------

.. cmake:macro:: my_macro(<param1> <param2>)
                 my_other_macro()

    This macro does crazy things.
    
    :param <param1>:
        This is a parameter
    :arg <param2>:
        This is an other parameter


.. cmake:function:: my_function(<param1> <param2> SOURCES <source1>... [OPTIONAL] [DISPLAY_NAME <name> [FINAL]])

  This function does the same, but supports much fancier arguments.


.. cmake:function:: no_args_func

    This function has no documented arguments.


.. cmake::function::empty_arglist_func()

    This function has an empty argument list.


.. cmake::function:: not_indexed()
    :noindex:

    This function should not appear in any index.


.. cmake:function:: not_listed_on_index
    :noindexentry:
    
    This function should be referencable but not appear in any index.


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


Indices
-------

* :ref:`genindex`
* :ref:`cmake-index`
