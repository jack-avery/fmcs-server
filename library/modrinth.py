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
        required: false
        type: dict
    datapacks:
        description: dict (converted yml) of datapacks to get download links for
        required: false
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
    datapacks:
      ketkets-player-shops:
"""

RETURN = r"""
response:
    mods: list of dict (format: [{"name": "name", "link": "<link>"}, ...])
    datapacks: list of dict (format same as above)
"""

from ansible.module_utils.basic import *
import requests


def get_modrinth_project(project) -> dict:
    req = requests.get(f"https://api.modrinth.com/v2/project/{project}")
    if req.status_code == 404:
        return None
    return req.json()


def get_modrinth_version(
    project: str, game_version: str, version: str = None, loader: str = None
) -> dict:
    mod = requests.get(
        f"https://api.modrinth.com/v2/project/{project}/version"
        + (f"/{version}" if version else "")
        + (f'?game_versions=["{game_version}"]' if game_version else "")
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

    mod = get_modrinth_version(name, game_version, loader=loader)
    if not mod:
        raise ValueError(f"{name} is not available for {game_version}-{loader}")

    return mod[0]["files"][0]["url"]


def main():
    fields = {
        "game_version": {"required": True, "type": "str"},
        "loader": {"required": True, "type": "str"},
        "mods": {"required": False, "type": "dict"},
        "datapacks": {"required": False, "type": "dict"},
    }

    module = AnsibleModule(argument_spec=fields)

    mods = []
    datapacks = []
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
            mods.append({"name": mod, "link": mrpmod})

    for pack, info in module.params["datapacks"].items():
        if info:
            if "source" in info:
                continue

        mrdp = None
        try:
            mrdp = get_modrinth_dl(pack, module.params["game_version"], None)

        except ValueError as e:
            missing.append(str(e))

        if mrdp:
            datapacks.append({"name": pack, "link": mrdp})

    if len(missing) > 0:
        module.fail_json(", ".join(missing))

    module.exit_json(changed=True, mods=mods, datapacks=datapacks)


if __name__ == "__main__":
    main()
