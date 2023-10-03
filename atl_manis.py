#!/usr/bin/env python3
import json
import logging
import os
import requests
import shutil
import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_mrpack_mod(name: str, game_version: str, loader: str) -> dict:
    project = requests.get(f"https://api.modrinth.com/v2/project/{name}").json()
    version = requests.get(
        f'https://api.modrinth.com/v2/project/{name}/version?game_versions=["{game_version}"]&loaders=["{loader}"]'
    ).json()[0]["files"][0]

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
