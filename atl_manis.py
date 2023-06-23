import json
import os
import shutil
import yaml

AUTHOR = "raspy"


def make_atlauncher_manifest(
    minecraft_ver: str, forge_ver: str, name: str, author: str, mods: dict
) -> dict:
    manifest = {
        "minecraft": {
            "version": f"{minecraft_ver}",
            "modLoaders": [{"id": f"forge-{forge_ver}", "primary": True}],
        },
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": name,
        "author": author,
        "files": [],
        "overrides": "overrides",
    }

    for mod in mods:
        mod_manifest = {
            "projectID": mod["project"],
            "fileID": mod["file"],
            "required": True,
        }
        manifest["files"].append(mod_manifest)

    return manifest


def main():
    with open("group_vars/mc.yml") as group_yml:
        group_vars = yaml.safe_load(group_yml)

    minecraft_ver = group_vars["minecraft_ver"]
    forge_ver = group_vars["forge_ver"]

    host_vars = {}
    for file in os.listdir("host_vars"):
        if ".secret." in file:
            continue

        hostname = file[: -len(".yml")]

        with open(f"host_vars/{file}") as host_yml:
            host_vars[hostname] = yaml.safe_load(host_yml)

    for host in host_vars:
        for instance in host_vars[host]["instances"]:
            mods = instance["mods"]
            name = f"{host}-{instance['name']}"
            manifest = make_atlauncher_manifest(
                minecraft_ver, forge_ver, name, AUTHOR, mods
            )
            with open(f"out/manifest/manifest.json", "w") as file:
                file.write(json.dumps(manifest, indent=4))
            shutil.make_archive(f"out/{name}", "zip", "out/manifest")

    return 0


if __name__ == "__main__":
    main()
