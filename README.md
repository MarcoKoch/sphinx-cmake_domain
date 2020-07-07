# sphinx-cmake_domain

A Sphinx extension that adds a CMake domain.


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

| Setting                      |  Default value | Description                                         |
|------------------------------|----------------|-----------------------------------------------------|
| cmake_modules_show_extension | `False`        | Show the `.cmake` file extension after module names |


### Documenting variables

```rst
.. cmake:var:: MY_VARIABLE
  
  My first variable ever created!
```

The following fields are supported:

| Field       | Description                       |
|-------------|-----------------------------------|
| `:type:`    | Type of a cache variable          |
| `:default:` | Default value of a cache variable |


### Documenting macros/functions

```rst
.. cmake:macro:: my_macro(<param1> <param2> ...)

  This macro does crazy things.


.. cmake:function:: my_function(<param1> <param2> SOURCES <source1>... [OPTIONAL] [DISPLAY_NAME <name> [FINAL]])

  This function does the same, but supports much fancier arguments.
```

The following fields are supported:

| Field       | Description                                                                |
|-------------|----------------------------------------------------------------------------|
| `:param:`   | Documents a parameter. For example: `:param <param1>:` , `:param SOURCES:` |


### Documenting modules

```rst
.. cmake:module:: MyModule

  I wrote a module. This is it. I'm proud of it.
```

The module name may optionally have a `.cmake` extension. Whether the extension is displayed or not is controlled by the `cmake_modules_show_extension` configuration setting, regardless of whether it is present in the definition.


### Referencing CMake entities

All CMake entities can be referenced using the `:any:` role. In addition to that, the following roles are supported:

| Role             | Description                |
|------------------|----------------------------|
| `:cmake:var:`    | Links to a variable        |
| `:cmake:func:`   | Links to a macro/function  |
| `:cmake:macro:`  | Synonym for `:cmake:func:` |
| `:cmake:module:` | Links to a module          |


## License

This extension is provided as open-source software under the 3-Clause BSD license. See file [LICENSE](LICENSE) for further information.


## Bugs, Feedback & Support

Reports and requests are welcome at <https://github.com/marcokoch/sphinx-cmake_domain/issues>.
Please use the search function before you post to avoid duplicate issues.


## Contributing

Pull requests are highly appreciated on [GitHub](https://github.com/marcokoch/sphinx-cmake_domain).


## Similar software

This extension is similar to the [sphinxcontrib-cmakedomain](https://github.com/sphinx-contrib/cmakedomain) extension. The latter seems to be no longer developed, though, and does not work with recent Sphinx versions. Also, this extension has some additional features over sphinxcontrib-cmakedomain and does not depend on any other packages except Sphinx.


## Contact

If your request does not fit into the issue tracker, please drop me an E-mail at <marco-koch@t-online.de>.

Please note that I'm developing this extension in my spare time. It may thus take a while until I find the time to answer. If you don't hear back within two weeks, feel free to send me a reminder.