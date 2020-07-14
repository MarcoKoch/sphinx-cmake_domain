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

from sphinx.addnodes import desc_annotation, desc_name, desc_optional, \
    desc_parameter, desc_parameterlist, desc_signature
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


def _get_index_sort_str(name, env):
    """
    Returns a string by which an entity with the given name shall be sorted in
    indices.
    """
    
    ignored_prefixes = env.config.cmake_index_common_prefix
    for prefix in ignored_prefixes:
        if name.startswith(prefix):
            return name[len(prefix):]
    
    return name


class CMakeEntityDescription(ObjectDescription):
    """Base class for directives documenting CMake entities"""
    
    has_content = True
    required_arguments = 1
    allow_nesting = False
    
    option_spec = {
        "noindex": directives.flag,
        "noindexentry": directives.flag
    }
    
    
    def set_signode_attributes(self, signode, name):
        signode["cmake:name"] = name
        signode["cmake:type"] = self.entity_type
    
    
    def handle_signature(self, sig, signode):    
        # By default, just use the complete signature as entity name.
        # Subclasses for entities with more complex signatures (e.g. functions)
        # should override this implementation.
        signode += desc_name(text = sig)
        self.set_signode_attributes(signode, sig)
        
        return sig
    
    
    def add_target_and_index(self, name, sig, signode):
        domain = self.env.get_domain("cmake")
        node_id = domain.make_entity_node_id(name, self.entity_type,
            self.state.document)
        signode["ids"].append(node_id)
        
        if "noindex" not in self.options:
            add_to_index = not "noindexentry" in self.options
        
            # Register the node at the domain, so it can be cross-referenced and
            # appears in the CMake index
            domain.add_entity(name, self.entity_type, node_id, signode,
                add_to_index)
        
            # Add an entry in the global index
            if add_to_index:
                key = _get_index_sort_str(name, self.env)[0].upper()
                index_text = "{} ({})".format(
                    name, domain.object_types[self.entity_type].lname)
                self.indexnode["entries"].append(
                    ("single", index_text, node_id, "", key))
    

class CMakeVariableDescription(CMakeEntityDescription):
    """Directive describing a CMake variable."""
    
    doc_field_types = [
        Field("type", names = ["type",], label = _("Type"), has_arg = False),
        Field("default", names = ("default",), label = _("Default value"),
            has_arg = False)
    ]
    
    entity_type = "variable"


class CMakeFunctionDescription(CMakeEntityDescription):
    """Directive describing a CMake macro/function"""
    
    doc_field_types = [
        GroupedField("parameter",
            names =["param", "parameter", "arg", "argument", "keyword",
                "option"],
            label = _("Parameters"), rolename = "param")
    ]
    
    entity_type = "function"
    
    
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
        Parses macro/function parameters from the relevant part of a
        macro/function signature.
        
        Returns a list of dictionaries with the following entries:
        
        * {type, name}      # for type == argument and type == keyword
        * {type}            # for type == elipsis
        * {type, subparams} # for type == optional_paramlist
        """
        
        # TODO: Handle multiple choice parameters like (A|B)
        
        parsed_params = []
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
                
                parsed_params.append({
                    "type": "optional_paramlist",
                    "subparams": cls._parse_parameter_list(
                        params_sig[start_pos + 1 : pos - 1])
                })
                continue
                    
            # All other types of parameters can be parsed using a regular
            # expression
            match = cls._param_regex.match(params_sig, pos)
            if match is None:
                raise cls._ParameterParseError(params_sig)
            
            matched_groups = match.groupdict()
            if matched_groups["argument"] is not None:
                parsed_params.append({
                    "type": "argument",
                    "name": match["argument"]
                })
            elif matched_groups["keyword"] is not None:
                parsed_params.append({
                    "type": "keyword",
                    "name": match["keyword"]
                })
            elif matched_groups["elipsis"] is not None:
                parsed_params.append({"type": "elipsis"})
            elif matched_groups["optional_paramlist"] is not None:
                parsed_params.append({
                    "type": "optional_paramlist",
                    "subparams": cls._parse_parameter_list(
                        match["optional_paramlist"])
                })
                
            pos = match.end()
        
        return parsed_params
    
    
    @classmethod
    def _add_param_nodes(cls, root_node, parsed_params):
        """
        Adds doctree nodes for the given parsed parameters (as returned by
        _parse_parameter_list()) as children to a given root node.
        """
       
        for param in parsed_params:
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
        
        self.set_signode_attributes(signode, name)
        
        paramlist_node = desc_parameterlist() 
        paramlist_node.child_text_separator = " "     
        if params is not None:
            try:
                parsed_params = self._parse_parameter_list(params)
            except self._ParameterParseError as ex:
                errmsg = (__("Invalid argument list for macro/function %s: %s") %
                    (name, ex.signature))
                if ex.message:
                    errmsg += "\n" + ex.message;
                _logger.error(errmsg, location = signode)

                signode += desc_name(text = sig)
                return name

            self._add_param_nodes(paramlist_node, parsed_params)
        
        signode += desc_name(text = name)
        signode += paramlist_node
        
        return name


class CMakeIndex(Index):
    """An index for CMake entities"""
    
    name = "index"
    localname = _("CMake Index")
    shortname = _("CMake")
    
    
    def generate(self, docnames = None):
        # name -> [entity_type, node_id, docname]
        entries = defaultdict(list)
        for name, entity_type, node_id, docname, add_to_index in self.domain.entities:
            if add_to_index:
                entries[name].append((entity_type, node_id, docname))
        
        # Sort by index name
        entries = sorted(entries.items(), key = lambda entry: 
                    _get_index_sort_str(entry[0], self.domain.env))
        
        # key -> [dispname, subtype, docname, anchor, extra, qualifier,
        #   description]
        content = defaultdict(list)
        for name, data in entries:
            key = _get_index_sort_str(name, self.domain.env)[0].upper()
            if len(data) > 1:
                # There are multiple entity descriptions with the same name.
                # Create an 'empty' toplevel entry with a sub-entry for each
                # entity description.
                content[key].append((name, 1, "", "", "", "", ""))
                
                for entity_type, node_id, docname in data:
                    type_str = self.domain.object_types[entity_type].lname
                    content[key].append((name, 2, docname, node_id, type_str,
                        "", ""))
            else:
                # There is only one entry with this name
                entity_type, node_id, docname = data[0]
                type_str = self.domain.object_types[entity_type].lname
                content[key].append((name, 0, docname, node_id, type_str,
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
        "function": CMakeFunctionDescription
    }
    object_types = {
        "variable": ObjType(_("CMake variable"), "var"),
        "function": ObjType(_("CMake macro/function"), "macro", "function"),
        "module": ObjType(_("CMake module"), "module")
    }
    initial_data = {
        "entities": {
            "variable": defaultdict(list), # name -> [(node_id, docname, add_to_index)]
            "function": defaultdict(list), # name -> [(node_id, docname, add_to_index)]
            "module": defaultdict(list), # name -> [(node_id, docname, add_to_index)]
        }
    }
    roles = {
        "var": XRefRole(),
        "func": XRefRole(),
        "macro": XRefRole(),
        "module": XRefRole(),
        "param": XRefRole()
    }
    
    
    # Maps the type of a xref role to the entity type referenced by that role
    # (as used in object_types).
    _xref_type_to_entity_type = {
        "var": "variable",
        "func": "function",
        "macro": "function",
        "module": "module"
    }
    
    
    @property
    def entities(self):
        entities = []
        for entity_type in self.data["entities"].keys():
            for name, descriptions in self.data["entities"][entity_type].items():
                entities += [(name, entity_type, node_id, docname, add_to_index)
                    for node_id, docname, add_to_index in descriptions]

        return entities
    
    
    def make_entity_node_id(self, name, entity_type, document):
        """Generates a node ID for an entity description"""
        
        node_id = make_id(self.env, document, "cmake",
            "-".join([entity_type, name]))
        
        # If there is already an other description for the same entity in the
        # current document, we append a number to make the ID unique. This
        # allows us to reference the individual descriptions from the indices.
        alias_cnt = len(self.data["entities"][entity_type][name])
        if alias_cnt != 0:
            node_id += "-" + str(alias_cnt)
        
        return node_id
    
    
    def add_entity(self, name, entity_type, node_id, location, add_to_index):
        """Called by our directives to register a documented entity."""

        self.data["entities"][entity_type][name].append(
            (node_id, self.env.docname, add_to_index))
    
    
    def get_full_qualified_name(self, node):
        return "cmake.{}.{}".format(node["cmake:type"], node["cmake:name"])
    
    
    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
            contnode):
        # :cmake:param: roles do not refer to entities but to macro/function
        # parameters. We thus need some special treatment here.
        if typ == "param":
            # TODO
            return
        
        # For all other roles, we simply look up the target object in the
        # list of registered entity descriptions for the respective entity type
        # of the given role.
        entity_type = self._xref_type_to_entity_type[typ]
            
        for name, descriptions in self.data["entities"][entity_type].items():
            if name == target and len(descriptions[0]) != 0:
                node_id, docname, _ = descriptions[0]
                label = " ".join([self.object_types[entity_type].lname, name])
                return make_refnode(builder, fromdocname, docname, node_id,
                    contnode, label)
        
        return None


def setup(app):
    """This function is called by Sphinx when loading the extension"""
    
    # Initialize localization
    package_dir = path.abspath(path.dirname(__file__))
    locale_dir = path.join(package_dir, "locales")
    app.add_message_catalog("sphinx-cmake_domain", locale_dir)
    
    # Register config settings
    app.add_config_value("cmake_index_common_prefix", [], "env")
    
    # Register our domain
    app.add_domain(CMakeDomain)
    
    # Return extension metadata
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True
    }
