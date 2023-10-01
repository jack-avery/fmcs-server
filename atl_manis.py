#!/usr/bin/env python3
import json
import logging
import os
import re
import requests
import shutil
import yaml

CURSEFORGE_RE = re.compile(
    r"https://www\.curseforge\.com/api/v1/mods/(\d+)/files/(\d+)/download"
)

AUTHOR = "raspy_on_osu"
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def make_atlauncher_manifest(
    minecraft_ver: str, loader: str, name: str, author: str, mods: dict
) -> dict:
    manifest = {
        "minecraft": {
            "version": f"{minecraft_ver}",
            "modLoaders": [{"id": f"{loader}", "primary": True}],
        },
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": name,
        "author": author,
        "files": [],
        "overrides": "overrides",
    }

    for name, mod in mods.items():
        if mod["mode"] == "server":
            continue

        if CURSEFORGE_RE.match(mod["source"]):
            project = CURSEFORGE_RE.findall(mod["source"])[0][0]
            file = CURSEFORGE_RE.findall(mod["source"])[0][1]
            mod_manifest = {
                "projectID": project,
                "fileID": file,
                "required": True,
            }
            manifest["files"].append(mod_manifest)

        else:
            file = requests.get(mod["source"])
            open(f"out/_/overrides/mods/{name}.jar", "wb").write(file.content)

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

        os.mkdir("out/_")
        os.mkdir("out/_/overrides")
        os.mkdir("out/_/overrides/mods")
        os.mkdir("out/_/overrides/resourcepacks")

        for instance in instances:
            minecraft_ver = instance["minecraft_ver"]
            if "fabric" in instance:
                loader = f"fabric-{instance['fabric']['version']}"
            elif "forge" in instance:
                loader = f"forge-{instance['forge']['version']}"
            mods = instance["mods"]
            name = f"{host}-{instance['name']}"

            manifest = make_atlauncher_manifest(
                minecraft_ver, loader, name, AUTHOR, mods
            )
            with open(f"out/_/manifest.json", "w") as file:
                file.write(json.dumps(manifest, indent=4))

            shutil.make_archive(f"out/{name}", "zip", "out/_")
            logging.info(f"{name} completed")

            # clean up for next
            shutil.rmtree("out/_")

    logging.info(f"Done")
    return 0


if __name__ == "__main__":
    main()
