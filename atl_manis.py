#!/usr/bin/env python3
import json
import logging
import os
import requests
import shutil
import yaml

from library.modrinth import get_modrinth_project, get_modrinth_version

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

CACHE = {}


def get_mrpack_file(name: str, game_version: str, loader: str = None) -> dict:
    if not (project := dict.get(CACHE, name, None)):
        logging.info(f"Getting project info for {name}...")
        project = get_modrinth_project(name)
        if not project:
            raise ValueError(f"{name} does not exist on modrinth")
        CACHE[name] = project
    else:
        logging.info(f"~ Using cached project info for {name}...")

    match project["project_type"]:
        case "mod":
            folder = "mods"
        case "shader":
            folder = "shaderpacks"

            # verify shader has loader
            # shaders are processed after mods, so this should be ok
            shader_has_loader = False
            for l in project["loaders"]:
                if l in CACHE:
                    shader_has_loader = True
                    break
            if not shader_has_loader:
                raise ValueError(
                    f"shader {name} missing loader! valid loaders are ({', '.join(project['loaders'])})"
                )
        case "resourcepack":
            folder = "resourcepacks"

    if not (version := dict.get(CACHE[name], f"{game_version}-{loader}", None)):
        logging.info(f"... and info on {game_version}-{loader}...")
        mod = get_modrinth_version(name, game_version, loader)
        if not mod:
            raise ValueError(f"{name} is not available for {game_version}-{loader}")
        version = mod[0]["files"][0]
        CACHE[name][f"{game_version}-{loader}"] = version
    else:
        logging.info(f"~ ... and cached info on {game_version}-{loader}...")

    return {
        "path": f"{folder}/{version['filename']}",
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


def make_mrpack(
    minecraft_ver: str,
    loader: str,
    name: str,
    mods: dict = None,
    resource_packs: dict = None,
    shaders: dict = None,
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

    if mods:
        for name, info in mods.items():
            if info:
                # curseforge, discord links, etc.
                if "source" in info:
                    file = requests.get(info["source"])
                    open(f"out/_/overrides/mods/{name}.jar", "wb").write(file.content)

            manifest["files"].append(
                get_mrpack_file(name, minecraft_ver, loader["type"])
            )

    if resource_packs:
        for name, info in resource_packs.items():
            if info:
                # curseforge, discord links, etc.
                if "source" in info:
                    file = requests.get(info["source"])
                    open(f"out/_/overrides/resourcepacks/{name}.zip", "wb").write(
                        file.content
                    )
                    shutil.unpack_archive(
                        f"out/_/overrides/resourcepacks/{name}.zip",
                        f"out/_/overrides/resourcepacks/{name}",
                        "zip",
                    )
                    os.remove(f"out/_/overrides/resourcepacks/{name}.zip")

            manifest["files"].append(get_mrpack_file(name, minecraft_ver))

    if shaders:
        for name, info in shaders.items():
            if info:
                # curseforge, discord links, etc.
                if "source" in info:
                    file = requests.get(info["source"])
                    open(f"out/_/overrides/shaderpacks/{name}.zip", "wb").write(
                        file.content
                    )

        manifest["files"].append(get_mrpack_file(name, minecraft_ver))

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
            mods = dict.get(instance, "mods", None)
            resource_packs = dict.get(instance, "resource_packs", None)
            shaders = dict.get(instance, "shaders", None)
            name = f"{host}-{instance['name']}"

            manifest = make_mrpack(
                minecraft_ver, loader, name, mods, resource_packs, shaders
            )
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
