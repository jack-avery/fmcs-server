#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r"""
---
module: narrow
short_description: todo
options:
author:
    - raspy
"""

EXAMPLES = r"""
- name: todo
"""

RETURN = r"""
response:
    description: todo
    type:
    returned:
    sample:
"""

from ansible.module_utils.basic import *


def main():
    fields = {
        "items": {"required": True, "type": "list"},
        "items_secrets": {"required": True, "type": "list"},
        "narrow": {"required": True, "type": "str"},
        "base_port": {"required": True, "type": "int"},
        "rsrv_port": {"required": True, "type": "int"},
        "inventory_hostname": {"required": True, "type": "str"},
        "groups": {"required": True, "type": "dict"},
        "hostvars": {"required": True, "type": "dict"},
    }

    module = AnsibleModule(argument_spec=fields)

    try:
        instances = []
        narrow = (
            module.params["narrow"].split(" ")
            if len(module.params["narrow"]) > 0
            else False
        )
        secrets = {f"{i['name']}": i for i in module.params["items_secrets"]}

        current_ip = module.params["hostvars"][module.params["inventory_hostname"]]["ansible_host"]

        for i, instance in enumerate(module.params["items"]):
            if not narrow or instance["name"] in module.params["narrow"]:
                port = module.params["base_port"] + (module.params["rsrv_port"] * i)
                if "port" in instance:
                    port = instance["port"]

                instances.append(
                    dict(
                        instance, **{
                            "port": port,
                            "secrets": secrets[instance["name"]]
                        }
                    )
                )

        if len(instances) == 0:
            raise ValueError("ONLY matches no instance names")

    except Exception as e:
        return module.fail_json({"err": e.__str__()})

    module.exit_json(
        changed=True,
        instances=instances
    )


if __name__ == "__main__":
    main()
