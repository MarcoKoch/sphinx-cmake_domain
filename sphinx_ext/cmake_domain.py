# This file is part of the sphinx-cmake_domain Sphinx extension.
# See <https://github.com/marcokoch/sphinx-cmake_comain> for recent information.
#
# # Copyright 2020 Marco Koch
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import re
from collections import defaultdict
from importlib.metadata import version, PackageNotFoundError
from os import path

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.addnodes import (
    desc_annotation, desc_name, desc_optional, desc_parameter,
    desc_parameterlist, desc_signature)
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index, ObjType
from sphinx.locale import get_translation
from sphinx.roles import XRefRole
from sphinx.util.docfields import Field, GroupedField
from sphinx.util.logging import getLogger
from sphinx.util.nodes import (
    get_node_line, get_node_source, make_id, make_refnode, traverse_parent)


try:
    __version__ = version("sphinx-cmake_domain")
except PackageNotFoundError:
    # The package is not installed
    from setuptools_scm import get_version
    __version__ = get_version(root = "..", relative_to = __file__)


# Optional extension for module names
_module_ext = ".cmake"


message_catalog = "sphinx-cmake_domain"
_ = get_translation(message_catalog)
__ = get_translation(message_catalog, "console")


_logger = getLogger(__name__)


# Helper functions
# -------------------------------------------------------------

def _get_index_sort_str(env, name):
    """
    Returns a string by which an object with the given name shall be sorted in
    indices.
    """
    
    ignored_prefixes = env.config.cmake_index_common_prefix
    for prefix in ignored_prefixes:
        if name.startswith(prefix) and name != prefix:
            return name[len(prefix):]
    
    return name


def _register_node(app, node_type):
    """Helper function for registering our custom node types."""
    
    formats = ["html", "latex", "text", "man", "texinfo"]
    
    tuples = {}
    for output_format in formats:
        tuples[output_format] = (
            lambda tr, node, fmt = output_format: visit_node(tr, node, fmt),
            lambda tr, node: depart_node(tr, node))
    
    app.add_node(node_type, **tuples)


# Doctree nodes
# -------------------------------------------------------------

# <-- Insert rant about Sphinx' horrible translator API here --->


# For macro/function descriptions we use some custom nodes instead of the
# builtin ones (desc_parameter etc.), since the builtin translaters produce
# output that is not well suited for the syntax common in CMake world. Using
#custom nodes allows us to provide our own translation logic instead of fiddling
# with internal details of Sphinx' builtin translators. This makes us more less
# dependent on the Sphinx version and is more friendly to users who use their
# own translators.


class desc_cmake_parameterlist(desc_parameterlist):
    """
     Doctree node similar to :cls:`sphinx.addnodes.desc_parameterlist` that
    generates output which is better suited for CMake macro/function parameter
    lists.
    
    Nodes of this class can't be nested.
    """
    
    child_text_separator = " "


class desc_cmake_parameter(desc_parameter):
    """
    Doctree node similar to :cls:`sphinx.addnodes.desc_parameter` that
    generates output which is better suited for CMake macro/function parameter
    lists.
    """
    
    pass


class desc_cmake_keyword(desc_cmake_parameter):
    """
    Doctree node for a single keyword in a CMake macro/function parameter list.
    
    Nodes of this class can only appear in a :cls:`desc_cmake_parameterlist`.
    """
    
    pass


class desc_cmake_optional(desc_optional):
    """
    Doctree node similar to :cls:`sphinx.addnodes.desc_optional` that generates
    output which better suited for CMake macro/function parameter lists.
    
    Nodes of this class can only appear in a :cls:`desc_cmake_parameterlist`.
    """
    
    child_text_separator = " "
    
    
    def astext(self):
        return "[{}]".format(super().astext())


class desc_cmake_group(nodes.Part, nodes.Inline, nodes.FixedTextElement):
    """
    Doctree node for a group of CMake macro/function parameters.
    
    This is used to for complex parameter descriptions such as
    ``OPTION|(KEYWORD <values>...)``.
    
    Nodes of this class can only appear in a :cls:`desc_cmake_parameterlist`.
    """
    
    child_text_separator = " "
    
    
    def astext(self):
        return "({})".format(super().astext())


class desc_cmake_choice(nodes.Part, nodes.Inline, nodes.FixedTextElement):
    """
    Doctree node for a choice of multiple CMake macro/function parameters
    such as ``OPTION_A|OPTION_B``.
    
    Nodes of this class can only appear in a :cls:`desc_cmake_parameterlist`.
    """
    
    child_text_separator = "|"
    
    
    def astext(self):
        return "|".join(child.astext() for child in self.children)


class TranslatorState:
    """
    Implements translation logic for our custom nodes.
    
    An instance of this class gets injected into the Sphinx translator.
    We do this instead of providing an entirely own set of translators since
    the latter would be incompatible with other extensions using custom
    translators. Furthermore, this solution should provide some out-of-the-box
    support for user-defined translators and non-standard output formats.
    
    For simplicity, this same class is used for all output formats.
    """
    
    @property
    def translator(self):
        """The translator to which this state belongs."""
        
        return self._translator
        
    
    @property
    def output_format(self):
        """The output format of :attr:`translator`."""
    
        return self._output_format
    
    
    @property
    def _param_separator(self):
        """
        The current parameter seperator for a given output format.
        
        If no seperation is needed, an empty string is returned.
        """
        
        return "" if self._first_param else self._param_seperator_stack[-1]


    def __init__(self, translator, output_format):
        self._translator = translator
        self._output_format = output_format
    
        # A stack of seperators for use between parameter-style nodes.
        # Entries are dictionaries mapping output formats to seperator strings.
        # If no string is provided for a specific output format, the mapping
        # with key "generic" is used (i.e. such key should always be present).
        self._param_seperator_stack = [" "]
        
        # True if the next parameter is the first in a group
        self._first_param = False
    
        # Current desc_cmake_parameterlist node. None if not inside such node.
        self._paramlist_node = None
    
    
    def _output(self, output):
        """
        Outputs *output* to *translator* using the standard API of the builtin
        translator for output format *output_format*.
        
        This is mainly to work around the fact that Sphinx' builtin translator
        for the plein text format uses a different API than all others.
        """
        
        if self.output_format == "text":
            self.translator.add_text(output)
        else:
            self.translator.body.append(output)
    
    
    def _check_in_parameterlist(self, current_node):
        """
        Logs an error and raises :cls:`docutils.nodes.SkipNode` if called
        outside a :cls:`desc_cmake_parameterlist node.
        """
    
        if not self._paramlist_node:
            _logger.error(
                _("A node of type {node_type} was encountered outside a "
                        "{paramlist_node_type}.").format(
                    node_type = type(node),
                    paramlist_node_type = desc_cmake_parameterlist),
                location = current_node)
            
            raise nodes.SkipNode()
    
    
    def _handle_basic_parameter_visit(self, node):
        """
        Implements some basic logic shared by the visitor functions for
        parameter-style nodes.
        """
        
        self._check_in_parameterlist(node)
        
        if self._param_separator:
            self._output(self._param_separator)
        
        self._first_param = False
    
    
    def visit_desc_cmake_parameterlist(self, node):
        """Visitor function for :cls:`desc_cmake_parameterlist`."""
        
        if self._paramlist_node is not None:
            _logger.error(
                __("Encountered nested {paramlist_node_type} nodes. "
                        "Outer node defined here: {source_file}, {line}").format(
                    paramlist_node_type = desc_cmake_parameterlist,
                    source_file = get_node_source(self._paramlist_node),
                    line = get_node_line(self._paramlist_node)),
                location = node)
            raise nodes.SkipNode()
        
        self._paramlist_node = node
        self._first_param = True
        
        if self.output_format == "html":
            self._output('<span class="sig-paren">(</span>')
        elif self.output_format == "latex":
            self._output('}{')
        else:
            self._output("(")
    
    
    def depart_desc_cmake_parameterlist(self, node):
        """Depart function for :cls:`desc_cmake_parameterlist`."""
        
        self._paramlist_node = None
        
        if self.output_format == "html":
            self._output('<span class="sig-paren">)</span>')
        elif self.output_format == "latex":
            self._output("}{")
        else:
            self._output(")")
    
    
    def visit_desc_cmake_parameter(self, node):
        """Visitor function for :cls:`desc_cmake_parameter`."""
        
        self._handle_basic_parameter_visit(node)
        
        if not node.hasattr("noemph"):
            if self.output_format == "html":
                self._output('<em class="sig-param sig-cmake-param">')
            elif self.output_format == "latex":
                self._output(r"\emph{")
    
    
    def depart_desc_cmake_parameter(self, node):
        """Depart function for :cls:`desc_cmake_parameter`."""
        
        if not node.hasattr("noemph"):
            if self.output_format == "html":
                self._output("</em>")
            elif self.output_format == "latex":
                self._output("}")
    
    
    def visit_desc_cmake_keyword(self, node):
        """Visitor function for :cls:`desc_cmake_keyword`."""
        
        if self.output_format == "html":
            self._handle_basic_parameter_visit(node)
        
            if not node.hasattr("noemph"):
                self._output(
                    '<em class="sig-param sig-cmake-param sig-cmake-keyword">')
        else:
            self.visit_desc_cmake_parameter(node)
    
    
    def depart_desc_cmake_keyword(self, node):
        """Depart function for :cls:`desc_cmake_keyword`."""
        
        self.depart_desc_cmake_parameter(node)
    
    
    def visit_desc_cmake_optional(self, node):
        """Visitor function for :cls:`desc_cmake_optional`."""
        
        self._handle_basic_parameter_visit(node)
        
        self._param_seperator_stack.append(node.child_text_separator)
        self._first_param = True
        
        if self.output_format == "html":
            self._output('<span class="optional cmake-optional">[</span>')
        elif self.output_format == "latex":
            self._output(r"\sphinxoptional{")
        else:
            self._output("[")
    
    
    def depart_desc_cmake_optional(self, node):
        """Depart function for :cls:`desc_cmake_optional`."""
        
        del self._param_seperator_stack[-1]
    
        if self.output_format == "html":
            self._output('<span class="optional cmake-optional">]</span>')
        elif self.output_format == "latex":
            self._output("}")
        else:
            self._output("]")
    
    
    def visit_desc_cmake_group(self, node):
        """Visitor function for :cls:`desc_cmake_group`."""
        
        self._handle_basic_parameter_visit(node)
        
        self._param_seperator_stack.append(node.child_text_separator)
        self._first_param = True
        
        if self.output_format == "html":
            self._output('<span class="sig-cmake-paramgrp">(</span>')
        elif self.output_format == "latex":
            self._output(r"\sphinxcmakeparamgrp{")
        else:
            self._output("(")
    
    
    def depart_desc_cmake_group(self, node):
        """Depart function for :cls:`desc_cmake_group`."""
        
        del self._param_seperator_stack[-1]
        
        if self.output_format == "html":
            self._output('<span class="sig-cmake-paramgrp">)</span>')
        elif self.output_format == "latex":
            self._output("}")
        else:
            self._output(")")
    
    
    def visit_desc_cmake_choice(self, node):
        """Visitor function for :cls:`desc_cmake_choice`."""
        
        self._handle_basic_parameter_visit(node)
        self._first_param = True
        
        if self.output_format == "html":
            self._param_seperator_stack.append(
                '<span class="sig-cmake-choice">|</span>')
        elif self.output_format == "latex":
            self._param_seperator_stack.append("}{")
            self._output(r"\sphinxcmakechoice{")
        else:
            self._param_seperator_stack.append("|")
    
    
    def depart_desc_cmake_choice(self, node):
        """Depart function for :cls:`desc_cmake_choice`."""
        
        del self._param_seperator_stack[-1]
        
        if self.output_format == "latex":
            self._output("}")


def visit_node(translator, node, output_format):
    """
    Generic node visitor function.
    
    This makes sure that *translator* has an instance of :cls:`TranslatorState`
    as its :attr:`!cmake_state` attribute and calls the respective
    :func:`!visit_XXX` function on that.
    """
    
    if not hasattr(translator, "cmake_state"):
        translator.cmake_state = TranslatorState(translator, output_format)
    
    method = getattr(translator.cmake_state, "visit_" + type(node).__name__)
    method(node)


def depart_node(translator, node):
    """
    Generic node depart function.
    
    This calls the respective :func:`!depart_XXX` function on
    ``translator.cmake_state``.
    """
    
    if not hasattr(translator, "cmake_state"):
        _logger.error(
            __("depart_node() called on this node without previous call to "
                "visit_node() with the same translator"),
            location = node)
        raise nodes.SkipNode()
    
    method = getattr(translator.cmake_state, "depart_" + type(node).__name__)
    method(node)


# Directives
# -------------------------------------------------------------

class CMakeObjectDescription(ObjectDescription):
    """Base class for directives documenting CMake objects"""
    
    has_content = True
    required_arguments = 1
    allow_nesting = False
    
    option_spec = {
        "noindex": directives.flag,
        "noindexentry": directives.flag
    }
    
    
    @property
    def object_type(self):
        raise NotImplementedError()
    
    
    def handle_signature(self, sig, signode):
        domain = self.env.get_domain("cmake")
    
        # By default, just use the entire signature as object name
        name = sig
        dispname = domain.make_object_display_name(name, self.object_type)
        
        signode += desc_name(text = dispname)
        return name
    
    
    def add_target_and_index(self, name, sig, signode):
        domain = self.env.get_domain("cmake")
        
        # Set the node ID that is used for referencing the node
        node_id = make_id(self.env, self.state.document, "cmake", name)
        signode["ids"].append(node_id)        
        self.state.document.note_explicit_target(signode)
              
        # Register the node at the domain, so it can be cross-referenced and
        # appears in the CMake index
        add_to_index = "noindexentry" not in self.options
        domain.register_object(name, self.object_type, node_id, add_to_index,
            signode)
    
        # Add an entry in the global index
        if add_to_index:
            type_str = domain.get_type_name(
                domain.object_types[self.object_type])
            dispname = domain.make_object_display_name(name, self.object_type)
            index_text = "{} ({})".format(dispname, type_str)
            key = _get_index_sort_str(self.env, dispname)[0].upper()
            self.indexnode["entries"].append(
                ("single", index_text, node_id, "", key))
    

class CMakeVariableDescription(CMakeObjectDescription):
    """Directive describing a CMake variable."""
    
    doc_field_types = [
        Field("type", names = ["type",], label = _("Type"), has_arg = False),
        Field("default", names = ("default",), label = _("Default value"),
            has_arg = False)
    ]
    
    object_type = "variable"
    
    
    # Regex used to parse variable description signatures
    _sig_regex = re.compile(r'(?P<name>\w+)(?:\s+(?P<value>.+))?')
    
    
    def handle_signature(self, sig, signode):
        domain = self.env.get_domain("cmake")
    
        sig_match = self._sig_regex.fullmatch(sig)
        if sig_match is None:
            _logger.error(
                __("Invalid variable signature: {sig}").format(sig = sig),
                location = signode)
            raise ValueError
        
        name = sig_match["name"]
        value = sig_match["value"]
        dispname = domain.make_object_display_name(name, "variable")
        
        signode += desc_name(text = dispname)
        if value is not None:
            signode += desc_annotation(text = " = " + value)
        
        return name


class CMakeFunctionDescription(CMakeObjectDescription):
    """Directive describing a CMake macro/function"""
    
    doc_field_types = [
        GroupedField("parameter",
            names =["param", "parameter", "arg", "argument", "keyword",
                "option"],
            label = _("Parameters"))
    ]
    
    object_type = "function"
    
    
    # Basic regex used for parsing macro/function signatures
    _base_sig_regex = re.compile("\s*(?P<name>\w+)\s*\((?P<params>.*)\)\s*")
    
    # Regexes used for tokenizing a macro/function parameter list
    # token_type => regex, has_argument
    _param_token_regexes = {
        "argument": (re.compile("\s*<(\w+)>\s*"), True),
        "keyword": (re.compile("\s*(\w+)\s*"), True),
        "ellipsis": (re.compile("\s*\.\.\.\s*"), False),
        "group_start": (re.compile("\s*\(\s*"), False),
        "group_end": (re.compile("\s*\)\s*"), False),
        "optional_start": (re.compile("\s*\[\s*"), False),
        "optional_end": (re.compile("\s*\]\s*"), False),
        "choice": (re.compile("\s*\|\s*"), False)
    }
    
    
    class _ParamListParseError(Exception):
        """
        Exception thrown during signature parsing if a macro/function
        parameter list has invalid syntax.
        """
        
        pass
    
    
    class _ParamListTokenizationError(_ParamListParseError):
        """Exception thrown by :meth:`_tokenize_parameter_list`."""
        
        def __init__(self, unexcpected_text, pos):
            super().__init__(
                __("Unexpected text at column {pos}: {unexpected}").format(
                pos = pos, unexpected = unexcpected_text))
    
    
    class _ParamListUnexpectedTokenError(_ParamListParseError):
        """Exception thrown on unexpected parameter list tokens."""
        
        def __init__(self, unexpected_token, pos):
            super().__init__(
                __("Unexpected token at position {pos}: "
                    "{raw} ({token_type})").format(
                pos = pos, raw = unexpected_token[1],
                token_type = unexpected_token[0]))
    
    
    @classmethod
    def _tokenize_parameter_list(cls, params):
        """
        Tokenizes a CMake macro/function parameter description using the token
        descriptions in _param_token_regexes.
        
        Returns a list of tuples of:
        
        * (token_type, raw, argument) for tokens that have an argument
        * (token_type, raw)           for tokens that do not have an argument
        """
    
        pos = 0
        while pos < len(params):
            token_recognized = False
        
            for token_type, (regex, has_argument) in (
                    cls._param_token_regexes.items()):
                match = regex.match(params, pos)
                if match is None:
                    continue
                
                if has_argument:
                    yield token_type, match[0].strip(), match[1]
                else:
                    yield token_type, match[0].strip()
                
                token_recognized = True
                pos = match.end()
                break
            
            if not token_recognized:
                raise cls._ParamListTokenizationError(params[pos:], pos)
    
    
    @classmethod
    def _parse_parameters(cls, tokenized_params, root_node):
        """
        Parses a tokenized parameters as returned by
        :meth:`_tokenize_parameter_list` and appends corresponding doctree nodes
        to the given root node.
        """
                
        # Temporary storage for nested nodes
        stack = [root_node]
        
        for i, token in enumerate(tokenized_params):
            new_stack_frame = False
        
            if token[0] == "argument":
                stack[-1] += desc_cmake_parameter(
                    text = "<{}>".format(token[2]))
                
            elif token[0] == "keyword":
                stack[-1] += desc_cmake_keyword(text = token[2])
                
            elif token[0] == "ellipsis":
                if len(stack[-1].children) == 0:
                    raise cls._ParamListUnexpectedTokenError(token, i)
                    
                stack[-1] += desc_annotation(text = "\u2026")
                
            elif token[0] == "group_start":
                stack.append(desc_cmake_group())
                stack[-2] += stack[-1]
                new_stack_frame = True
                
            elif token[0] == "group_end":
                if type(stack[-1]) != desc_cmake_group:            
                    raise cls._ParamListUnexpectedTokenError(token, i)
                
                child_cnt = len(stack[-1].children)                
                if child_cnt == 1:
                    # Replace the group with the single contained element
                    stack[-1].parent.replace(stack[-1], stack[-1].children[0])
                elif child_cnt == 0:
                    # Remove the group
                    stack[-1].parent -= stack[-1]
                    
                del stack[-1]
                
            elif token[0] == "optional_start":
                stack.append(desc_cmake_optional())
                stack[-2] += stack[-1]                
                new_stack_frame = True
                
            elif token[0] == "optional_end":
                if type(stack[-1]) != desc_cmake_optional:
                    raise cls._ParamListUnexpectedTokenError(token, i)
                
                child_cnt = len(stack[-1].children)
                if child_cnt == 0:
                    # Remove empty optional
                    stack[-1].parent -= stack[-1]
                elif (child_cnt == 1
                        and type(stack[-1].children[0]) == desc_cmake_group):
                    # If the only child is a group, we can place the content of
                    # that group directly into the optional node
                    group = stack[-1].children[0]
                    stack[-1] += group.children
                    stack[-1] -= group
                    
                del stack[-1]
                
            elif token[0] == "choice":
                if (type(stack[-1]) == desc_cmake_choice
                        or len(stack[-1].children) == 0):
                    raise cls._ParamListUnexpectedTokenError(token, i)
                    
                prev = stack[-1].children[-1] # Previous node
                if type(prev) == desc_cmake_choice:
                    # Put the choice node back on top of the stack, so the next
                    # node gets added to it
                    stack.append(prev)
                else:
                    # Wrap prev in a desc_cmake_choice
                    stack.append(desc_cmake_choice())
                    prev.parent.replace(prev, stack[-1])
                    stack[-1] += prev
                
                new_stack_frame = True
                    
            else:
                assert False, "Unknown token type: " + token[0]
            
            # desc_cmake_choice is different from other grouping nodes in the
            # sense that we do not add child nodes to it until an ending token
            # is encountered, but only add it to the to of the stack if a choice
            # token is encountered and then add a single node defined by the
            # following token. After this token we remove the desc_cmake_choice
            # from the stack again.
            frame_index = -2 if new_stack_frame else -1
            if type(stack[frame_index]) == desc_cmake_choice:
                del stack[frame_index]
        
        if len(stack) > 1:
            raise cls._ParamListParseError(
                __("Unexpected end of parameter list"))
    
    
    def handle_signature(self, sig, signode):
        base_match = self._base_sig_regex.fullmatch(sig)
        if base_match is None:
            _logger.error(
                __("Invalid macro/function signature: {sig}".format(sig = sig)),
                location = signode)
            raise ValueError
        
        name = base_match["name"]
        params = base_match["params"]
        
        paramlist = desc_cmake_parameterlist()
        paramlist.child_text_separator = " "
        
        try:
            tokenized_params = self._tokenize_parameter_list(params)
            self._parse_parameters(tokenized_params, paramlist)
        except self._ParamListParseError as ex:
            _logger.error(
                __("Failed to parse parameters for macro/function {name}: "
                    "{msg}").format(name = name, msg = str(ex)),
                location = signode)
            raise ValueError
        
        signode += desc_name(text = name)
        signode += paramlist
        
        return name


class CMakeModuleDescription(CMakeObjectDescription):
    """Directive describing a CMake module."""
    
    object_type = "module"
    
    
    def handle_signature(self, sig, signode):
    
        # The module name may be specified with a '.cmake' extension.
        # We remove that extension for our internal naming
        name = sig
        if name.endswith(_module_ext):
            name = name[:-len(_module_ext)]
        
        # Now we re-add the extension for the display name if
        # cmake_modules_add_extension is enabled.
        dispname = name
        if self.env.app.config.cmake_modules_add_extension:
            dispname += _module_ext
        
        signode += desc_name(text = dispname)
        return name


class CMakeTargetDescription(CMakeObjectDescription):
    """Directive describing a CMake build target."""
    
    object_type = "target"


# Roles
# -------------------------------------------------------------

class CMakeModuleXRefRole(XRefRole):
    """
    Special xref role for referencing CMake module descriptions.
    
    This makes sure to handle the file extension correctly.
    """
    
    def process_link(self, env, refnode, has_explicit_title, title, target):
        # Add the file extension to the title
        if (not title.endswith(_module_ext) and 
                self.env.app.config.cmake_modules_add_extension):
            title += _module_ext
    
        # Remove the file extension from the target
        if target.endswith(_module_ext):
            target = target[:-len(_module_ext)]
        
        return title, target


# Index
# -------------------------------------------------------------

class CMakeIndex(Index):
    """An index for CMake entities."""
    
    name = "index"
    localname = _("CMake Index")
    shortname = _("CMake")
    
    
    def generate(self, docnames = None):
        # name -> [obj_type, node_id, docname]
        entries = defaultdict(list)
        for name, obj_type, node_id, docname, add_to_index in (
                self.domain.objects):
            if add_to_index and (docnames is None or docname in docnames):
                entries[name].append((obj_type, node_id, docname))
        
        # Sort by index name
        entries = sorted(entries.items(),
            key = lambda entry: _get_index_sort_str(self.domain.env, entry[0]))
        
        # key -> [dispname, subtype, docname, anchor, extra, qualifier,
        #   description]
        content = defaultdict(list)
        for name, data in entries:
            key = _get_index_sort_str(self.domain.env, name)[0].upper()
            if len(data) > 1:
                # There are multiple object descriptions with the same name.
                # Create an 'empty' toplevel entry with a sub-entry for each
                # description.
                content[key].append((name, 1, "", "", "", "", ""))
                
                for obj_type, node_id, docname in data:
                    dispname = self.domain.make_object_display_name(
                        name, obj_type)             
                    type_str = self.domain.get_type_name(
                        self.domain.object_types[obj_type])
                    content[key].append((dispname, 2, docname, node_id,
                        type_str, "", ""))
            else:
                # There is only one entry with this name
                obj_type, node_id, docname = data[0]
                dispname = self.domain.make_object_display_name(name, obj_type)
                type_str = self.domain.get_type_name(
                    self.domain.object_types[obj_type])
                content[key].append((dispname, 0, docname, node_id, type_str,
                    "", ""))
        
        # Sort by keys
        content = sorted(content.items())
        
        return content, False


# Domain
# -------------------------------------------------------------

class CMakeDomain(Domain):
    """A Sphinx domain for documenting CMake entities."""
    
    name = "cmake"
    label = _("CMake")
    data_version = 0
    indices = [CMakeIndex]
    directives = {
        "var": CMakeVariableDescription,
        "macro": CMakeFunctionDescription,
        "function": CMakeFunctionDescription,
        "module": CMakeModuleDescription,
        "target": CMakeTargetDescription
    }
    object_types = {
        "variable": ObjType(_("variable"), "var"),
        "function": ObjType(_("macro/function"), "macro", "func"),
        "module": ObjType(_("module"), "mod"),
        "target": ObjType(_("target"), "tgt")
    }
    initial_data = {
        # type -> name -> (node_id, docname, add_to_index)
        "objects": defaultdict(dict)
    }
    roles = {
        "var": XRefRole(),
        "func": XRefRole(fix_parens = True),
        "macro": XRefRole(fix_parens = True),
        "mod": CMakeModuleXRefRole(),
        "tgt": XRefRole()
    }
    
    
    # Maps the type of a xref role to the entity type referenced by that role
    # (as used in object_types).
    _xref_type_to_object_type = {
        "var": "variable",
        "func": "function",
        "macro": "function",
        "mod": "module",
        "tgt": "target"
    }
    
    
    @property
    def objects(self):
        for obj_type, type_entries in self.data["objects"].items():
            for name, (node_id, docname, add_to_index) in type_entries.items():
                yield (name, obj_type, node_id, docname, add_to_index)
    
    
    def get_objects(self):    
        #fullname, dispname, type, docname, anchor, priority
        for name, obj_type, node_id, docname, add_to_index in self.objects:
            dispname = self.make_object_display_name(name, obj_type)
            yield (name, dispname, obj_type, docname, node_id, 1)
    
    
    def _warn_duplicate_object(self, name, obj_type, location):
        """
        Logs a warning that the given object is described in multiple locations.
        
        The location of the previous description is read from `self.data`.
        """
    
        dispname = self.make_object_display_name(name, obj_typ)
        type_str = self.get_type_name(self.object_types[obj_typ])
        other_docname = self.data["objects"][obj_type][name][1]
        
        _logger.warning(
            __("Duplicate description of {typ} {name}: "
                    "Previously described in {other_docname}. "
                    "Use :noindex: with one of them.").format(
                typ = type_str, name = dispname, other_docname = other_docname),
            location = location)
    
    
    def _make_refnode(self, env, name, obj_type, node_id, docname, builder,
            fromdocname, contnode):      
        """
        Helper function for generatinga  reference node linking to an object
        description.
        """
        
        title = "{}: {}".format(
            self.get_type_name(self.object_types[obj_type]), name)     
        return make_refnode(builder, fromdocname, docname, node_id, contnode,
            title)
    
    
    def make_object_display_name(self, name, obj_type):
        """Returns the displayed name for the given object."""
    
        # Display function names with parentheses if add_function_parentheses
        # is enabled
        if (obj_type == "function" 
                and self.env.app.config.add_function_parentheses):
            return name + "()"
        
        # Display module names with file extension if
        # cmake_modules_add_extension is enabled
        if (obj_type == "module" 
                and self.env.app.config.cmake_modules_add_extension):
            return name + _module_ext
        
        return name
    
    
    def register_object(self, name, obj_type, node_id, add_to_index, location):
        """Called by our directives to register a documented entity."""
        
        if not obj_type in self.object_types:
            raise Exception(
                __("'{str}' is not a known CMake object type").format(
                    str = obj_type))
        
        if name in self.data["objects"][obj_type]:
            self._warn_duplicate_object(self, name, location)
            return

        self.data["objects"][obj_type][name] = (
            node_id, self.env.docname, add_to_index)
    
    
    def clear_doc(self, docname):
        for obj_type in self.object_types.keys():
            for name, (_, obj_docname, _) in (
                    list(self.data["objects"][obj_type].items())):
                if obj_docname == docname:
                    del self.data["objects"][obj_type][name] 
    
    
    def merge_domaindata(self, docnames, otherdata):
        for obj_type in self.object_types.keys():
            for name, obj in otherdata["objects"][obj_type].items():
                if obj[1] in docnames:
                    if name in self.data["objects"][obj_type]:
                        self._warn_duplicate_object(name, obj_type, location)
                        continue
                
                    self.data["objects"][obj_type][name] = obj
    
    
    def resolve_xref(self, env, fromdocname, builder, xref_type, target, node,
            contnode):
        obj_type = self._xref_type_to_object_type[xref_type]    
        
        for name, (node_id, docname, _) in (
                self.data["objects"][obj_type].items()):
            if name == target:
                return self._make_refnode(env, name, obj_type, node_id, docname,
                    builder, fromdocname, contnode)
        
        return None
    
    
    def resolve_any_xref(self, env, fromdocname, builder, target, node,
            contnode):
            
        # Macro/functions may be specified with empty parentheses
        if target.endswith("()"):
            target = target[:-2]
            resolved = self.resolve_xref(env, fromdocname, builder, "func",
                target, node, contnode)
            return ([(self.name + ":func", resolved)] if resolved is not None 
                else [])
        
        # Module names may be specified with a file extension
        if target.endswith(_module_ext):
            target = target[:-len(_module_ext)]
            resolved = self.resolve_xref(env, fromdocname, builder, "mod",
                target, node, contnode)
            return ([(self.name + ":mod", resolved)] if resolved is not None
                else [])
        
        # If we can't determine the entity type from the target string,
        # try all entity types
        resolved_nodes = []
        for _, obj_type_obj in self.object_types.items():
            role = obj_type_obj.roles[0]
            resolved = self.resolve_xref(env, fromdocname, builder, role,
                target, node, contnode)
            if resolved is not None:
                resolved_nodes.append((":".join([self.name, role]), resolved))
        
        return resolved_nodes


# Extension setup
# -------------------------------------------------------------

def setup(app):
    """Called by Sphinx when loading the extension."""
    
    # Initialize localization
    package_dir = path.abspath(path.dirname(__file__))
    locale_dir = path.join(package_dir, "locale")
    app.add_message_catalog(message_catalog, locale_dir)
    
    # Register config settings
    app.add_config_value("cmake_index_common_prefix", [], "env")
    app.add_config_value("cmake_modules_add_extension", False, "env")
    
    # Register custom doctree nodes
    _register_node(app, desc_cmake_parameterlist)
    _register_node(app, desc_cmake_parameter)
    _register_node(app, desc_cmake_keyword)
    _register_node(app, desc_cmake_optional)
    _register_node(app, desc_cmake_group)
    _register_node(app, desc_cmake_choice)
    
    # Register our domain
    app.add_domain(CMakeDomain)
    
    # Return extension metadata
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True
    }

