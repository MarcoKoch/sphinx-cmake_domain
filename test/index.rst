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
    :noindexentry:

    This variable should be referencable but not appear in any index.


Referencing CMake entities
--------------------------

Variables
~~~~~~~~~

This links :any:`MY_VARIABLE` using ``:any:``.

This links :any:`MY_CACHE_VARIABLE` using ``:any:``.

This links :any:`MY_OPTION` using ``:any:``.

This links :any:`NOT_LISTED_ON_INDEX` using ``:any:``.

This links :cmake:var:`MY_VARIABLE` using ``:cmake:var:``.

This links :cmake:var:`MY_CACHE_VARIABLE` using ``:cmake:var:``.

This links :cmake:var:`MY_OPTION` using ``:cmake:var:``.

This links :cmake:var:`NOT_LISTED_ON_INDEX` using ``:cmake:var:``.


Indices
-------

* :ref:`genindex`
* :ref:`cmake-index`
