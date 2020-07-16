# sphinx-cmake_domain

A [Sphinx](https://www.sphinx-doc.org) extension that adds a [CMake](https://cmake.org) domain.


## Installation

TODO


## Usage

### Enabling the extension

In your `conf.py` add:

```python
extensions = [
  "sphinx_ext.cmake_comain",
  # ...
]
```


### Configuration

*sphinx-cmake_domain* adds the following config settings:

| Setting                     | Default value | Description                                                                    |
|-----------------------------|---------------|--------------------------------------------------------------------------------|
| cmake_modules_add_extension | `False`       | Show the `.cmake` file extension after module names                            |
| cmake_index_common_prefix   | `[]`          | A list of prefixes that will be ignored when sorting CMake objects in an index |

Additionally, the following standard settings are supported:

* [add_function_parentheses](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-add_function_parentheses)
* [html_domain_indices](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_domain_indices)


### Documenting variables

```rst
.. cmake:var:: MY_VARIABLE
  
  My first variable ever created!


.. cmake:var:: MY_OTHER_VARIABLE "value"

  This one even has a value!
```

The following options are supported:

| Option           | Description                                                                       |
|------------------|-----------------------------------------------------------------------------------|
| `:noindexentry:` | Don't add this variable description to the index                                  |
| `:noindex:`      | Don't allow cross-referencing this variable description. Implies `:noindexentry:` |

The following doc fields are supported:

| Field       | Description                       |
|-------------|-----------------------------------|
| `:type:`    | Type of a cache variable          |
| `:default:` | Default value of a cache variable |


### Documenting macros/functions

```rst
.. cmake:macro:: my_macro(<param1> <param2>)

  This macro does crazy things.


.. cmake:function:: my_function(<param1> <param2> SOURCES <source1>... \
                      [OPTIONAL] (EITHER|OR) [THIS|THAT] [DISPLAY_NAME <name> [FINAL]])

  This function does the same, but supports much fancier arguments.
```

Directives `cmake:macro` and `cmake:functions` are aliases for each other.


The following options are supported:

| Option           | Description                                                                             |
|------------------|-----------------------------------------------------------------------------------------|
| `:noindexentry:` | Don't add this macro/function description to the index                                  |
| `:noindex:`      | Don't allow cross-referencing this macro/function description. Implies `:noindexentry:` |

The following doc fields are supported:

| Field                 | Description                                                                |
|-----------------------|----------------------------------------------------------------------------|
| `:param:`<sup>1</sup> | Documents a parameter. For example: `:param <param1>:` , `:param SOURCES:` |

<sup>1</sup> Aliases are: `:parameter:`, `:arg:`, `:argument:`, `:keyword:` and `:option:`


### Documenting modules

```rst
.. cmake:module:: MyModule

  I wrote a module. This is it. I'm proud of it.
```

The module name may optionally have a `.cmake` extension. Whether the extension is displayed or not is controlled by the `cmake_modules_add_extension` configuration setting, regardless of whether it is present in the definition.

The following options are supported:

| Option           | Description                                                                     |
|------------------|---------------------------------------------------------------------------------|
| `:noindexentry:` | Don't add this module description to the index                                  |
| `:noindex:`      | Don't allow cross-referencing this module description. Implies `:noindexentry:` |


### Referencing CMake objects

All CMake objects can be referenced using the `:any:` role. In addition to that, the following roles are supported:

| Role           | Description               |
|----------------|---------------------------|
| `:cmake:var:`  | Links to a variable       |
| `:cmake:func:` | Links to a macro/function |
| `:cmake:macro:`| Alias for `:cmake:func:`  |
| `:cmake:mod:`  | Links to a module         |

The target name for `:cmake:func:` and `:cmake:macro:` may be specified with or without trailing parentheses. Whether paraentheses are displayed solely depends on the value of the `add_function_parentheses` config setting.

The target name for `:cmake:mod` may be specified with or without the `.cmake` suffix. Whether the suffix is displayed solely depends on the value of the `cmake_modules_add_extension` configuration setting.


### CMake index

If the `html_domain_indices` config setting is enabled, an index of all documented CMake objects is generated in addition to the global index. The CMake index can be referenced using ``:ref:`cmake-index` ``.


## License

This extension is provided as open-source software under the 3-Clause BSD license. See file [LICENSE](LICENSE) for further information.


## Bugs, feedback & support

Reports and requests are welcome at <https://github.com/marcokoch/sphinx-cmake_domain/issues>.
Please use the search function before you post to avoid duplicate issues.


## Contributing

Pull requests are highly appreciated on [GitHub](https://github.com/marcokoch/sphinx-cmake_domain).


## Similar software

This extension is similar to the [sphinxcontrib-cmakedomain](https://github.com/sphinx-contrib/cmakedomain) extension. The latter seems to be no longer developed, though, and does not work with recent Sphinx versions. Also, this extension has some additional features over sphinxcontrib-cmakedomain and does not depend on any other packages except Sphinx.


## Contact

This software is developed by Marco Koch <marco-koch@t-online.de>.

Please note that I'm working on this extension in my spare time. It may thus take a while until I find the time to answer. If you don't hear back within two weeks, feel free to send me a reminder.

