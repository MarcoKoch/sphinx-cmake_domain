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
from os import path

from collections import defaultdict

from sphinx.addnodes import desc_name, desc_signature
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index, ObjType
from sphinx.locale import _, __
from sphinx.roles import XRefRole
from sphinx.util.logging import getLogger
from sphinx.util.docfields import Field
from sphinx.util.nodes import make_id, make_refnode


__version__ = "0.1.0.dev1"
__author__ = "Marco Koch"
__copyright__ = "Copyright 2020, Marco Koch"
__license__ = "BSD 3-Clause"


_logger = getLogger(__name__)


# Maps entity types (as used in CMakeDomain.data["entities"]) localized labels
_entity_type_labels = {
    "variable": _("CMake Variable"),
    "function": _("CMake Macro/Function"),
    "module": _("CMake Module")
}


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
    
    
    def handle_signature(self, sig, signode):
        # By default, just use the signature as entity name.
        # Subclasses for entities with more complex signatures (e.g. functions)
        # should override this implementation.
        signode += desc_name(text = sig)
        signode["cmake:name"] = sig
        signode["cmake:type"] = self.entity_type
        
        return sig
    
    
    def add_target_and_index(self, name_cls, sig, signode):
        node_id = make_id(self.env, self.state.document, "cmake.",
            ".".join([self.entity_type, sig]))
        signode["ids"].append(node_id)
        
        if "noindex" not in self.options:
            # Add an entry in the global index
            key = _get_index_sort_str(sig, self.env)[0].upper()
            index_text = "{} ({})".format(
                sig, _entity_type_labels[self.entity_type])
            self.indexnode["entries"].append(
                ("single", index_text, node_id, "", key))
            
            # Register the node at the domain, so it can be cross-referenced and
            # appears in the CMake index
            domain = self.env.get_domain("cmake")
            domain.add_entity(sig, self.entity_type, node_id, signode)
    

class CMakeVariableDescription(CmakeEntityDescription):
    """Directive describing a CMake variable."""
    
    doc_field_types = [
        Field("type", label = _("Type")),
        Field("default", label = _("Default value"))
    ]
    
    entity_type = "variable"


class CMakeIndex(Index):
    """An index for CMake entities"""
    
    name = "index"
    localname = _("CMake Index")
    shortname = _("CMake")
    
    
    def generate(self, docnames = None):
        entries = ([(_get_index_sort_str(entity[0], self.domain.env), entity)
            for entity in self.domain.entities])
        entries = sorted(entries, key = lambda entry: entry[0])
        
        content = defaultdict(list)
        for sort_str, (name, entity_type, node_id, docname) in entries:
            key = sort_str[0].upper()
            
            # dispname, subtype, docname, anchor, extra, qualifier, description
            content[key].append((name, 0, docname, node_id, docname, "",
                _entity_type_labels[entity_type]))
        
        return sorted(content.items()), True


class CMakeDomain(Domain):
    """A Sphinx domain for documenting CMake entities"""
    
    name = "cmake"
    label = _("CMake")
    data_version = 0
    directives = {"var": CMakeVariableDescription}
    indices = [CMakeIndex]
    object_types = {
        "variable": ObjType(_("variable"), "var")
    }
    initial_data = {
        "entities": {
            "variable": {}, # name -> node_id, docname
            "function": {}, # name -> node_id, docname
            "module": {}, # name -> node_id, docname
        }
    }
    roles = {
        "var": XRefRole(),
        "func": XRefRole(),
        "macro": XRefRole(),
        "module": XRefRole()
    }
    
    
    # Maps the type of a xref role to the entity type referenced by that role
    # (as used in self.data["entities"]).
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
            entities += [(name, entity_type, node_id, docname)
                for name, (node_id, docname) 
                in self.data["entities"][entity_type].items()]

        return entities
    
    
    def add_entity(self, name, entity_type, node_id, location):
        """Called by our directives to register a documented entity."""
        
        if name in self.data["entities"][entity_type]:
            other = self.data["entities"][entity_type][name]
            _logger.warning(
                __("Duplicate description of %s %s. "
                    "Previously defined in: %s. "
                    "Use :noindex: for one of the descriptions."),
                _entity_type_labels[entity_type], name, other[2],
                location=location)
        
        self.data["entities"][entity_type][name] = (node_id, self.env.docname)
    
    
    def get_full_qualified_name(self, node):
        return "cmake.{}.{}".format(node["cmake:type"], node["cmake:name"])
    
    
    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
            contnode):
        entity_type = self._xref_type_to_entity_type[typ]
            
        for name, (node_id, docname) in self.data["entities"][entity_type].items():
            if name == target:
                return make_refnode(builder, fromdocname, docname, node_id,
                    contnode, " ".join([_entity_type_labels[entity_type], name]))
        
        return None


def setup(app):
    """This is called by Sphinx when loading the extension"""
    
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
        "env_version": 0,
        "parallel_read_safe": True,
        "parallel_write_safe": True
    }

