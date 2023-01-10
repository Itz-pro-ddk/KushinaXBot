"""Kushina plugin extender"""
# Copyright (C) 2020 - 2023  Kushina Team, <https://github.com/Itz-pro-ddk.git>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import importlib
import inspect
from types import ModuleType as PluginType
from typing import TYPE_CHECKING, Any, Iterable, MutableMapping, Optional, Type

from kushina import custom_plugins, plugin, plugins, util
from kushina.error import ExistingPluginError

from .kushina_mixin_base import MixinBase

if TYPE_CHECKING:
    from .kushina_bot import Kushina


class PluginExtender(MixinBase):
    # Initialized during instantiation
    plugins: MutableMapping[str, plugin.Plugin]

    def __init__(self: "Kushina", **kwargs: Any) -> None:
        # Initialize plugin map
        self.plugins = {}

        # Propagate initialization to other mixins
        super().__init__(**kwargs)

    def load_plugin(
        self: "Kushina", cls: Type[plugin.Plugin], *, comment: Optional[str] = None
    ) -> None:
        self.log.info(f"Loading {cls.format_desc(comment)}")

        if cls.name in self.plugins:
            old = type(self.plugins[cls.name])
            raise ExistingPluginError(old, cls)

        plug = cls(self)
        plug.comment = comment
        self.register_listeners(plug)
        self.register_commands(plug)
        self.plugins[cls.name] = plug

    def unload_plugin(self: "Kushina", plug: plugin.Plugin) -> None:
        cls = type(plug)
        self.log.info(f"Unloading {plug.format_desc(plug.comment)}")

        self.unregister_listeners(plug)
        self.unregister_commands(plug)
        del self.plugins[cls.name]

    def _load_all_from_metaplug(
        self: "Kushina", subplugins: Iterable[PluginType], *, comment: Optional[str] = None
    ) -> None:
        for plug in subplugins:
            for sym in dir(plug):
                cls = getattr(plug, sym)
                if inspect.isclass(cls) and issubclass(cls, plugin.Plugin) and not cls.disabled:
                    self.load_plugin(cls, comment=comment)

    # noinspection PyTypeChecker,PyTypeChecker
    def load_all_plugins(self: "Kushina") -> None:
        self.log.info("Loading plugins")
        self._load_all_from_metaplug(plugins.subplugins)
        self._load_all_from_metaplug(custom_plugins.subplugins, comment="custom")
        self.log.info("All plugins loaded.")

    def unload_all_plugins(self: "Kushina") -> None:
        self.log.info("Unloading plugins...")

        # Can't modify while iterating, so collect a list first
        for plug in list(self.plugins.values()):
            self.unload_plugin(plug)

        self.log.info("All plugins unloaded.")

    async def reload_plugin_pkg(self: "Anjani") -> None:
        self.log.info("Reloading base plugin class...")
        await util.run_sync(importlib.reload, plugin)

        self.log.info("Reloading master plugin...")
        await util.run_sync(importlib.reload, plugins)

        self.log.info("Reloading custom master module...")
        await util.run_sync(importlib.reload, custom_plugins)
