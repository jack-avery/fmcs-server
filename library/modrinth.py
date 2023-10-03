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
        description: List of Modrinth mods
        required: true
        type: list
author:
    - raspy (github.com/jack-avery)
"""

EXAMPLES = r"""
- name: Get mod download links
  modrinth:
    game_version: "1.20.1"
    loader: "fabric"
    mods:
      - sodium
      - lithium
"""

RETURN = r"""
response:
    dls: list of dict (format: [{"name": "name", "link": "<link>"}, ...])
"""

from ansible.module_utils.basic import *
import requests


def get_mrpack_mod(name: str, game_version: str, loader: str) -> dict:
    project = requests.get(f"https://api.modrinth.com/v2/project/{name}")

    if project.status_code == 404:
        raise ValueError(f"{name} does not exist on modrinth")
    project = project.json()
    if project["server_side"] == "unsupported":
        return None

    mod = requests.get(
        f'https://api.modrinth.com/v2/project/{name}/version?game_versions=["{game_version}"]&loaders=["{loader}"]'
    ).json()
    if len(mod) == 0:
        raise ValueError(f"mod {mod} is not available for {game_version}-{loader}")

    return mod[0]["files"][0]["url"]


def main():
    fields = {
        "game_version": {"required": True, "type": "str"},
        "loader": {"required": True, "type": "str"},
        "mods": {"required": True, "type": "list"},
    }

    module = AnsibleModule(argument_spec=fields)

    dls = []
    for mod in module.params["mods"]:
        try:
            mrpmod = get_mrpack_mod(
                mod, module.params["game_version"], module.params["loader"]
            )
        except ValueError as e:
            return module.fail_json(str(e))

        if mrpmod:
            dls.append({"name": mod, "link": mrpmod})

    module.exit_json(changed=True, dls=dls)


if __name__ == "__main__":
    main()
