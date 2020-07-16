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
from os import path

from docutils.parsers.rst import directives

from sphinx.addnodes import (
    desc_annotation, desc_name, desc_optional, desc_parameter,
    desc_parameterlist, desc_signature)
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index, ObjType
from sphinx.locale import _, __
from sphinx.roles import XRefRole
from sphinx.util.docfields import Field, GroupedField
from sphinx.util.logging import getLogger
from sphinx.util.nodes import make_id, make_refnode


__version__ = "0.1.0.dev1"
__author__ = "Marco Koch"
__copyright__ = "Copyright 2020, Marco Koch"
__license__ = "BSD 3-Clause"


_logger = getLogger(__name__)


# Optional extension for module names
_module_ext = ".cmake"


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
    
    
    def add_target_and_index(self, name, sig, signode):
        domain = self.env.get_domain("cmake")
        
        # Set the node ID that is used for referencing the node
        node_id = make_id(self.env, self.state.document, "", name)
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
            _logger.error(__("Invalid variable signature: %s"), sig,
                location = signode)
            signode += desc_name(text = sig)
            return sig
        
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
    
    
    # Regexes used to parse macro/function definitions
    _base_regex = re.compile(
        r"(?P<name>\w+)\s*(?:\(\s*(?P<paramlist>[^)]*)\s*\))?")
    _param_regex = re.compile(
        "(?:<(?P<argument>\w+)>)|"
        "(?P<keyword>\w+)|"
        "(?P<elipsis>\.\.\.)")
    _non_whitespace_regex = re.compile(r"[^\s]")
        
    
    class _ParameterParseError(Exception):
        """
        Exception thrown by _parse_parameter_list() if the given signature
        string is invalid.
        """
        
        @property
        def signature(self):
            return self._params_sig
        
        
        @property
        def message(self):
            return self._msg
        
        
        def __init__(self, params_sig, msg = None):
            super().__init__(__("Bad macro/function parameter signature"))
            self._params_sig = params_sig
            self._msg = msg
    
    
    @classmethod
    def _parse_parameter_list(cls, params_sig):
        """
        Parses macro/function parameters from a signature string.
        
        Returns an AST as list of dictionaries with the following entries:
        
        * {type, name}      # for type == "argument" or type == "keyword"
        * {type}            # for type == "elipsis"
        * {type, subparams} # for type == "optional_paramlist"
        """
        
        # TODO: Handle multiple choice parameters like (A|B)
        
        pos = 0
        sig_len = len(params_sig)
        while pos < sig_len:
            # Ignore whitespace between parameters
            non_whitespace_match = cls._non_whitespace_regex.search(
                params_sig, pos)
            if non_whitespace_match is None:
                break
            pos = non_whitespace_match.start()
            
            # Check if the next parameter is optional (i.e. enclosed in [])
            if params_sig[pos] == '[':
                # If so, find the matching closing ]
                start_pos = pos
                open_bracket_cnt = 1
                pos += 1
                while open_bracket_cnt > 0:
                    if pos >= sig_len:
                        raise cls._ParameterParseError(params_sig,
                            __("No matching closing bracket for optional "
                                "parameter list starting at column %i") %
                                    start_pos)
                
                    if params_sig[pos] == '[':
                        open_bracket_cnt += 1
                    elif params_sig[pos] == ']':
                        open_bracket_cnt -= 1
                        
                    pos += 1
                
                yield {
                    "type": "optional_paramlist",
                    "subparams": cls._parse_parameter_list(
                        params_sig[start_pos + 1 : pos - 1])
                }
                continue
                    
            # All other types of parameters can be parsed using a regular
            # expression
            match = cls._param_regex.match(params_sig, pos)
            if match is None:
                raise cls._ParameterParseError(params_sig)
            
            matched_groups = match.groupdict()
            if matched_groups["argument"] is not None:
                yield {
                    "type": "argument",
                    "name": match["argument"]
                }
            elif matched_groups["keyword"] is not None:
                yield {
                    "type": "keyword",
                    "name": match["keyword"]
                }
            elif matched_groups["elipsis"] is not None:
                yield {"type": "elipsis"}
            elif matched_groups["optional_paramlist"] is not None:
                yield {
                    "type": "optional_paramlist",
                    "subparams": cls._parse_parameter_list(
                        match["optional_paramlist"])
                }
                
            pos = match.end()
    
    
    @classmethod
    def _add_param_nodes(cls, root_node, ast):
        """
        Adds doctree nodes for the given parsed parameters (as returned by
        _parse_parameter_list()) as children to a given root node.
        """
       
        for param in ast:
            if param["type"] == "argument":
                root_node += desc_parameter(
                    text = "<{}>".format(param["name"]))
            elif param["type"] == "keyword":
                root_node += desc_parameter(text = param["name"])
            elif param["type"] == "elipsis":
                root_node += desc_annotation(text = "...")
            elif param["type"] == "optional_paramlist":            
                optional_node = desc_optional()
                cls._add_param_nodes(optional_node, param["subparams"])
                root_node += optional_node
    
    
    def handle_signature(self, sig, signode):
        base_match = self._base_regex.fullmatch(sig)
        if base_match is None:
            _logger.error(__("Invalid macro/function signature: %s"),
                sig, location = signode)
            signode += desc_name(text = sig)
            return sig
        
        name = base_match["name"]
        params = base_match["paramlist"]
        
        paramlist_node = desc_parameterlist() 
        paramlist_node.child_text_separator = " "     
        if params is not None:
            try:
                param_ast = self._parse_parameter_list(params)
            except self._ParameterParseError as ex:
                errmsg = (__("Invalid argument list for macro/function %s: %s") %
                    (name, ex.signature))
                if ex.message:
                    errmsg += "\n" + ex.message;
                _logger.error(errmsg, location = signode)

                signode += desc_name(text = sig)
                return name

            self._add_param_nodes(paramlist_node, param_ast)
        
        signode += desc_name(text = name)
        signode += paramlist_node
        
        return name


class CMakeModuleDescription(CMakeObjectDescription):
    """Directive describing a CMake module"""
    
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


class CMakeIndex(Index):
    """An index for CMake entities"""
    
    name = "index"
    localname = _("CMake Index")
    shortname = _("CMake")
    
    
    def generate(self, docnames = None):
        # name -> [typ, node_id, docname]
        entries = defaultdict(list)
        for name, typ, node_id, docname, add_to_index in self.domain.objects:
            if add_to_index:
                entries[name].append((typ, node_id, docname))
        
        # Sort by index name
        entries = sorted(entries.items(),
            key = lambda entry: _get_index_sort_str(self.domain.env, entry[0]))
        
        # key -> [dispname, subtype, docname, anchor, extra, qualifier,
        #   description]
        content = defaultdict(list)
        for name, data in entries:
            key = _get_index_sort_str(self.domain.env, name)[0].upper()
            if len(data) > 1:
                # There are multiple entity descriptions with the same name.
                # Create an 'empty' toplevel entry with a sub-entry for each
                # entity description.
                content[key].append((name, 1, "", "", "", "", ""))
                
                for typ, node_id, docname in data:
                    dispname = self.domain.make_object_display_name(name, typ)             
                    type_str = self.domain.get_type_name(
                        self.domain.object_types[typ])
                    content[key].append((dispname, 2, docname, node_id,
                        type_str, "", ""))
            else:
                # There is only one entry with this name
                typ, node_id, docname = data[0]
                dispname = self.domain.make_object_display_name(name, typ)
                type_str = self.domain.get_type_name(
                    self.domain.object_types[typ])
                content[key].append((dispname, 0, docname, node_id, type_str,
                    "", ""))
        
        # Sort by keys
        content = sorted(content.items())
        
        return content, False


class CMakeDomain(Domain):
    """A Sphinx domain for documenting CMake entities"""
    
    name = "cmake"
    label = _("CMake")
    data_version = 0
    indices = [CMakeIndex]
    directives = {
        "var": CMakeVariableDescription,
        "macro": CMakeFunctionDescription,
        "function": CMakeFunctionDescription,
        "module": CMakeModuleDescription
    }
    object_types = {
        "variable": ObjType(_("variable"), "var"),
        "function": ObjType(_("macro/function"), "macro", "func"),
        "module": ObjType(_("module"), "mod")
    }
    initial_data = {
        "variable": {}, # name -> (node_id, docname, add_to_index)
        "function": {}, # name -> (node_id, docname, add_to_index)
        "module": {}, # name -> (node_id, docname, add_to_index)
    }
    roles = {
        "var": XRefRole(),
        "func": XRefRole(fix_parens = True),
        "macro": XRefRole(fix_parens = True),
        "mod": CMakeModuleXRefRole()
    }
    
    
    # Maps the type of a xref role to the entity type referenced by that role
    # (as used in object_types).
    _xref_type_to_entity_type = {
        "var": "variable",
        "func": "function",
        "macro": "function",
        "mod": "module"
    }
    
    
    @property
    def objects(self):
        for typ in self.object_types.keys():
            for name, (node_id, docname, add_to_index) in self.data[typ].items():
                yield (name, typ, node_id, docname, add_to_index)
    
    
    def get_objects(self):    
        #fullname, dispname, type, docname, anchor, priority
        for typ in self.object_types.keys():
            for name, (node_id, docname, _) in self.data[typ].items():
                dispname = self.make_object_display_name(name, typ)
                yield (name, dispname, typ, docname, node_id, 1)
    
    
    def make_object_display_name(self, name, typ):
        """Returns the displayed name for the given object."""
    
        # Display function names with parentheses if add_function_parentheses
        # is enabled
        if typ == "function" and self.env.app.config.add_function_parentheses:
            return name + "()"
        
        # Display module names with file extension if
        # cmake_modules_add_extension is enabled
        if typ == "module" and self.env.app.config.cmake_modules_add_extension:
            return name + _module_ext
        
        return name
    
    
    def _warn_duplicate_objects(self, name, typ, location):
        """
        Logs a warning that the given object is described in multiple locations.
        
        The location of the previous description is read from `self.data`.
        """
    
        dispname = self.make_object_display_name(name, typ)
        type_str = self.get_type_name(self.object_types[typ])
        other_docname = self.data[typ][name][1]
        
        _logger.warning(
            __("Duplicate description of %s %s: Previously described in %s. "
                "Use :noindex: with one of them."),
            type_str, dispname, other_docname, location = location)
    
    
    def register_object(self, name, typ, node_id, add_to_index, location):
        """Called by our directives to register a documented entity."""
        
        if name in self.data[typ]:
            self._warn_duplicate_objects(self, name, location)
            return

        self.data[typ][name] = (node_id, self.env.docname, add_to_index)
    
    
    def clear_doc(self, docname):
        for typ in self.object_types.keys():
            for name, (_, obj_docname, _) in list(self.data[typ].items()):
                if obj_docname == docname:
                    del self.data[typ][name] 
    
    
    def merge_domaindata(self, docnames, otherdata):
        for typ in self.object_types.keys():
            for name, obj in otherdata[typ].items():
                if obj[1] in docnames:
                    if name in self.data[typ]:
                        self._warn_duplicate_objects(name, typ, location)
                        continue
                
                    self.data[typ][name] = obj
    
    
    def _make_refnode(self, env, name, typ, node_id, docname, builder,
            fromdocname, contnode):      
        """
        Helper function for generating reference nodes linking to entity
        descriptions.
        """
        
        title = "{}: {}".format(self.get_type_name(self.object_types[typ]),
            name)     
        return make_refnode(builder, fromdocname, docname, node_id, contnode,
            title)
    
    
    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
            contnode):
        typ = self._xref_type_to_entity_type[typ]    
        
        for name, (node_id, docname, _) in self.data[typ].items():
            if name == target:
                return self._make_refnode(env, name, typ, node_id, docname,
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
        for typ, obj_type in self.object_types.items():
            role = obj_type.roles[0]
            resolved = self.resolve_xref(env, fromdocname, builder, role,
                target, node, contnode)
            if resolved is not None:
                resolved_nodes.append((":".join([self.name, role]), resolved))
        
        return resolved_nodes


def setup(app):
    """This function is called by Sphinx when loading the extension"""
    
    # Initialize localization
    package_dir = path.abspath(path.dirname(__file__))
    locale_dir = path.join(package_dir, "locales")
    app.add_message_catalog("sphinx-cmake_domain", locale_dir)
    
    # Register config settings
    app.add_config_value("cmake_index_common_prefix", [], "env")
    app.add_config_value("cmake_modules_add_extension", False, "env")
    
    # Register our domain
    app.add_domain(CMakeDomain)
    
    # Return extension metadata
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True
    }
