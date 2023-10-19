#!/usr/bin/python
# -*- coding: utf-8 -*-

# https://github.com/jack-avery

DOCUMENTATION = r"""
---
module: modrinth
short_description: Grab list of Modrinth download links
options:
    game_version:
        description: Minecraft version
        required: true
        type: str
    loader:
        description: Mod loader type e.g. 'fabric', 'forge'
        required: true
        type: str
    mods:
        description: dict (converted yml) of Modrinth mods as configured in host_vars
        required: true
        type: dict
author:
    - raspy (github.com/jack-avery)
"""

EXAMPLES = r"""
- name: Get mod download links
  modrinth:
    game_version: "1.20.2"
    loader: "fabric"
    mods:
      sodium:
      lithium:
      sound-physics-remastered:
        source: (override link, checking this will be ignored!)
"""

RETURN = r"""
response:
    dls: list of dict (format: [{"name": "name", "link": "<link>"}, ...])
"""

from ansible.module_utils.basic import *
import requests


def get_modrinth_project(name) -> dict:
    project = requests.get(f"https://api.modrinth.com/v2/project/{name}")
    if project.status_code == 404:
        return None
    return project.json()


def get_modrinth_version(name: str, game_version: str, loader: str = None) -> dict:
    mod = requests.get(
        f'https://api.modrinth.com/v2/project/{name}/version?game_versions=["{game_version}"]'
        + (f'&loaders=["{loader}"]' if loader else "")
    ).json()
    if len(mod) == 0:
        return None
    return mod


def get_modrinth_dl(name: str, game_version: str, loader: str) -> dict:
    project = get_modrinth_project(name)
    if not project:
        raise ValueError(f"{name} does not exist on modrinth")
    if project["server_side"] == "unsupported":
        return None

    mod = get_modrinth_version(name, game_version, loader)
    if not mod:
        raise ValueError(f"mod {name} is not available for {game_version}-{loader}")

    return mod[0]["files"][0]["url"]


def main():
    fields = {
        "game_version": {"required": True, "type": "str"},
        "loader": {"required": True, "type": "str"},
        "mods": {"required": True, "type": "dict"},
    }

    module = AnsibleModule(argument_spec=fields)

    dls = []
    missing = []
    for mod, info in module.params["mods"].items():
        if info:
            # explicit client-only
            if "mode" in info:
                if info["mode"] == "client":
                    continue

            # has provided source URL; ignore
            if "source" in info:
                continue

        mrpmod = None
        try:
            mrpmod = get_modrinth_dl(
                mod, module.params["game_version"], module.params["loader"]
            )

        except ValueError as e:
            missing.append(str(e))

        if mrpmod:
            dls.append({"name": mod, "link": mrpmod})

    if len(missing) > 0:
        module.fail_json(", ".join(missing))

    module.exit_json(changed=True, dls=dls)


if __name__ == "__main__":
    main()
