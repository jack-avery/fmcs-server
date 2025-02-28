#!/usr/bin/env python3
import base64
import hashlib
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


def get_mrpack_file(
    name: str, game_version: str, version: str = None, loader: str = None
) -> dict:
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
            for loader in project["loaders"]:
                if loader in CACHE:
                    shader_has_loader = True
                    break
            if not shader_has_loader:
                raise ValueError(
                    f"shader {name} missing loader! valid loaders are ({', '.join(project['loaders'])})"
                )
        case "resourcepack":
            folder = "resourcepacks"

    if file := dict.get(CACHE[name], f"{game_version}-{loader}", None):
        logging.info(f"~~~ and cached info on {game_version}-{loader}...")
    elif version:
        logging.info(f"... and info on explicit version {version}...")
        mod = get_modrinth_version(name, None, version=version, loader=loader)
        if not mod:
            raise ValueError(f"{name} has no version {version}")
        file = mod["files"][0]
        CACHE[name][f"{game_version}-{loader}"] = file
    else:
        logging.info(f"... and info on {game_version}-{loader}...")
        mod = get_modrinth_version(name, game_version, version=version, loader=loader)
        if not mod:
            raise ValueError(f"{name} is not available for {game_version}-{loader}")
        file = mod[0]["files"][0]
        CACHE[name][f"{game_version}-{loader}"] = file

    return {
        "path": f"{folder}/{file['filename']}",
        "hashes": {
            "sha1": file["hashes"]["sha1"],
            "sha512": file["hashes"]["sha512"],
        },
        "env": {
            "server": project["server_side"],
            "client": project["client_side"],
        },
        "downloads": [file["url"]],
        "filesize": file["size"],
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
                if "mode" in info:
                    if info["mode"] == "server":
                        continue

                # curseforge, discord links, etc.
                if "source" in info:
                    file = requests.get(info["source"])
                    open(f"mrpacks/_/overrides/mods/{name}.jar", "wb").write(
                        file.content
                    )
                    continue

            manifest["files"].append(
                get_mrpack_file(name, minecraft_ver, loader=loader["type"])
            )

    if resource_packs:
        for name, info in resource_packs.items():
            if info:
                # curseforge, discord links, etc.
                if "version" in info:
                    manifest["files"].append(
                        get_mrpack_file(name, None, version=info["version"])
                    )
                    continue

            manifest["files"].append(get_mrpack_file(name, minecraft_ver))

    if shaders:
        for name, info in shaders.items():
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
    if not os.path.exists("mrpacks"):
        os.mkdir("mrpacks")
    if os.path.exists("mrpacks/_"):
        shutil.rmtree("mrpacks/_")

    for host in host_vars:
        instances = host_vars[host]["instances"]
        logging.info(
            f"{host} has {len(instances)} instance(s):\n -- "
            + ", ".join([i["name"] for i in instances])
        )

        for instance in instances:
            os.mkdir("mrpacks/_")
            os.mkdir("mrpacks/_/overrides")
            os.mkdir("mrpacks/_/overrides/mods")
            os.mkdir("mrpacks/_/overrides/resourcepacks")

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
            manifest_json = json.dumps(manifest, indent=4)
            with open("mrpacks/_/modrinth.index.json", "w") as file:
                file.write(manifest_json)
            manifest_hash = base64.urlsafe_b64encode(
                hashlib.sha256(manifest_json.encode("utf-8")).digest()
            )[:7].decode("ascii")

            # zip and rename to .mrpack so ATLauncher accepts it
            shutil.make_archive(f"mrpacks/{name}", "zip", "mrpacks/_")
            shutil.move(f"mrpacks/{name}.zip", f"mrpacks/{name}-{manifest_hash}.mrpack")
            # store hash separately for ansible to handle
            with open(f"mrpacks/{name}.hash", "w") as file:
                file.write(manifest_hash)

            logging.info(f"{name} completed")

            # clean up for next
            shutil.rmtree("mrpacks/_")

    logging.info("Done")
    return 0


if __name__ == "__main__":
    main()
