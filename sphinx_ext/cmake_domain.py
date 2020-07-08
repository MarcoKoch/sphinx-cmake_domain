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

from sphinx.addnodes import desc_name, desc_signature
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index, ObjType
from sphinx.locale import _, __
from sphinx.roles import XRefRole
from sphinx.util.docfields import Field
from sphinx.util.nodes import make_id, make_refnode


__version__ = "0.1.0.dev1"
__author__ = "Marco Koch"
__copyright__ = "Copyright 2020, Marco Koch"
__license__ = "BSD 3-Clause"


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
    


class CmakeEntityDescription(ObjectDescription):
    """Base class for directives documenting CMake entities"""
    
    has_content = True
    required_arguments = 1
    allow_nesting = False
    
    option_spec = {
        "noindex": directives.flag,
        "noindexentry": directives.flag
    }
    
    
    def handle_signature(self, sig, signode):
        # By default, just use the signature as entity name.
        # Subclasses for entities with more complex signatures (e.g. functions)
        # should override this implementation.
        signode += desc_name(text = sig)
        signode["cmake:name"] = sig
        signode["cmake:type"] = self.entity_type
        
        return sig
    
    
    def add_target_and_index(self, name_cls, sig, signode):
        domain = self.env.get_domain("cmake")
        node_id = domain.make_entity_node_id(sig, self.entity_type,
            self.state.document)
        signode["ids"].append(node_id)
        
        if "noindex" not in self.options:
            add_to_index = not "noindexentry" in self.options
        
            # Register the node at the domain, so it can be cross-referenced and
            # appears in the CMake index
            domain.add_entity(sig, self.entity_type, node_id, signode,
                add_to_index)
        
            # Add an entry in the global index
            if add_to_index:
                key = _get_index_sort_str(sig, self.env)[0].upper()
                index_text = "{} ({})".format(
                    sig, domain.object_types[self.entity_type].lname)
                self.indexnode["entries"].append(
                    ("single", index_text, node_id, "", key))
    

class CMakeVariableDescription(CmakeEntityDescription):
    """Directive describing a CMake variable."""
    
    doc_field_types = [
        Field("type", names = ("type",), label = _("Type"), has_arg = False),
        Field("default", names = ("default",), label = _("Default value"),
            has_arg = False)
    ]
    
    entity_type = "variable"


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
    directives = {"var": CMakeVariableDescription}
    indices = [CMakeIndex]
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
        "module": XRefRole()
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

