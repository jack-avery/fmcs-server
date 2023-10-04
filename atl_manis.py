#!/usr/bin/env python3
import json
import logging
import os
import shutil
import yaml

from library.modrinth import get_modrinth_mod, get_modrinth_mod_ver

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

CACHE = {}


def get_mrpack_mod(name: str, game_version: str, loader: str) -> dict:
    if not (project := dict.get(CACHE, name, None)):
        logging.info(f"Getting project info for {name}...")
        project = get_modrinth_mod(name)
        if not project:
            raise ValueError(f"{name} does not exist on modrinth")
        CACHE[name] = project
    else:
        logging.info(f"~ Using cached project info for {name}...")

    if not (version := dict.get(CACHE[name], f"{game_version}-{loader}", None)):
        logging.info(f"... and mod info on {game_version}-{loader}...")
        mod = get_modrinth_mod_ver(name, game_version, loader)
        if not mod:
            raise ValueError(f"mod {name} is not available for {game_version}-{loader}")
        version = mod[0]["files"][0]
        CACHE[name][f"{game_version}-{loader}"] = version
    else:
        logging.info(f"~ ... and cached mod info on {game_version}-{loader}...")

    return {
        "path": f"mods/{name}.jar",
        "hashes": {
            "sha1": version["hashes"]["sha1"],
            "sha512": version["hashes"]["sha512"],
        },
        "env": {
            "server": project["server_side"],
            "client": project["client_side"],
        },
        "downloads": [version["url"]],
        "filesize": version["size"],
    }


def make_atlauncher_manifest(
    minecraft_ver: str, loader: str, name: str, mods: dict
) -> dict:
    manifest = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": "1.0.0",
        "name": name,
        "files": [],
        "dependencies": {
            "minecraft": minecraft_ver,
            f"{loader['type']}-loader": loader["version"],
        },
    }

    for name in mods.keys():
        manifest["files"].append(get_mrpack_mod(name, minecraft_ver, loader["type"]))

    return manifest


def main():
    host_vars = {}
    for file in os.listdir("host_vars"):
        if ".sample" in file:
            continue

        if ".secret." in file:
            continue

        hostname = file[: -len(".yml")]

        with open(f"host_vars/{file}") as host_yml:
            host_vars[hostname] = yaml.safe_load(host_yml)
    logging.info(
        f"host_vars loaded w/ {len(host_vars)} host(s):\n -- "
        + ", ".join(host_vars.keys())
    )

    # verify file structure
    if not os.path.exists("out"):
        os.mkdir("out")
    if os.path.exists("out/_"):
        shutil.rmtree("out/_")

    for host in host_vars:
        instances = host_vars[host]["instances"]
        logging.info(
            f"{host} has {len(instances)} instance(s):\n -- "
            + ", ".join([i["name"] for i in instances])
        )

        for instance in instances:
            os.mkdir("out/_")
            os.mkdir("out/_/overrides")
            os.mkdir("out/_/overrides/mods")
            os.mkdir("out/_/overrides/resourcepacks")

            minecraft_ver = instance["minecraft_ver"]
            if "fabric" in instance:
                loader = {"type": "fabric", "version": instance["fabric"]}
            elif "forge" in instance:
                loader = {"type": "forge", "version": instance["forge"]}
            mods = instance["mods"]
            name = f"{host}-{instance['name']}"

            manifest = make_atlauncher_manifest(minecraft_ver, loader, name, mods)
            with open(f"out/_/modrinth.index.json", "w") as file:
                file.write(json.dumps(manifest, indent=4))

            # zip and rename to .mrpack so ATLauncher accepts it
            shutil.make_archive(f"out/{name}", "zip", "out/_")
            shutil.move(f"out/{name}.zip", f"out/{name}.mrpack")

            logging.info(f"{name} completed")

            # clean up for next
            shutil.rmtree("out/_")

    logging.info(f"Done")
    return 0


if __name__ == "__main__":
    main()
