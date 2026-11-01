# Name: Alex Wang  Student ID: 101377606
import sys
import json
import xml.etree.ElementTree as ET
import yaml


class InputFileError(Exception):
    """Raised when an input file is missing or not valid."""


class Device:
    """One device from the inventory."""

    def __init__(self, dev_id, role, os_version, owner, statuses):
        # save the info about this device
        self.dev_id = dev_id
        self.role = role
        self.os_version = os_version
        self.owner = owner
        self.statuses = statuses


def load_inventory(path):
    """Read the XML file. Return the site, the list of devices and the skipped count."""
    try:
        # open the file and read it as XML
        with open(path, "rb") as f:
            tree = ET.parse(f)
    except (OSError, ET.ParseError) as error:
        # turn any file problem into my own error with the file name in it
        raise InputFileError("Cannot read inventory file " + path + ": " + str(error))

    root = tree.getroot()
    # site is None if the attribute is missing
    site = root.get("site")
    devices = []
    skipped = 0

    # go through every device element
    for element in root.findall("device"):
        dev_id = element.get("id")
        # no id means skip this device and count it
        if dev_id is None:
            skipped += 1
            continue

        # owner stays None if there is no owner element
        owner = None
        owner_element = element.find("owner")
        if owner_element is not None:
            owner = owner_element.text

        # collect the status of every interface
        statuses = []
        for interface in element.findall("interface"):
            statuses.append(interface.get("status"))

        # make a Device object and add it to the list
        devices.append(Device(dev_id, element.get("role"), element.get("os"), owner, statuses))

    return site, devices, skipped


def load_policy(path):
    """Read the YAML file and return the policy as a dictionary."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            # safe_load only reads data, load could run code
            policy = yaml.safe_load(f)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise InputFileError("Cannot read policy file " + path + ": " + str(error))

    # an empty file gives None, which just means no checks
    if policy is None:
        return {}
    # the policy has to be a mapping (a dictionary)
    if not isinstance(policy, dict):
        raise InputFileError("Policy file " + path + " is not a mapping")
    return policy


def check_device(device, policy):
    """Return a list of the violations of one device."""
    violations = []

    # if min_os is not in the policy, the role and version checks are off
    min_os = policy.get("min_os")
    if isinstance(min_os, dict):
        # the role is not in min_os, so it is not allowed
        if device.role not in min_os:
            violations.append({"device": device.dev_id, "type": "unknown_role", "role": device.role})

    return violations


def build_report(site, devices, skipped, policy):
    """Count everything, check every device and return the report dictionary."""
    # these will hold the totals
    roles = {}
    interfaces = {"up": 0, "down": 0, "other": 0}
    violations = []
    compliant = []

    for device in devices:
        # add 1 to this role (get gives 0 the first time we see it)
        roles[device.role] = roles.get(device.role, 0) + 1

        # count the interfaces, anything that is not up or down goes in other
        for status in device.statuses:
            if status == "up":
                interfaces["up"] += 1
            elif status == "down":
                interfaces["down"] += 1
            else:
                interfaces["other"] += 1

        # check the device and keep its violations
        problems = check_device(device, policy)
        violations.extend(problems)
        # a device with no problems is compliant
        if len(problems) == 0:
            compliant.append(device.dev_id)

    # the report wants the ids in sorted order
    compliant.sort()
    return {
        "site": site,
        "total_devices": len(devices),
        "skipped_devices": skipped,
        "roles": roles,
        "interfaces": interfaces,
        "violations": violations,
        "compliant": compliant,
    }


def main(args):
    """Run the program and return the exit code."""
    # args[0] is pa2.py, so exactly two arguments means length 3
    if len(args) != 3:
        print("usage: python pa2.py DEVICES.xml POLICY.yaml")
        return 2

    try:
        # read both files, a bad file raises my InputFileError
        site, devices, skipped = load_inventory(args[1])
        policy = load_policy(args[2])
    except InputFileError as error:
        # show the message without a traceback and exit with code 1
        print("Error:", error)
        return 1

    report = build_report(site, devices, skipped, policy)
    # write the report to audit.json
    with open("audit.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # short summary on screen
    print("Devices:", report["total_devices"], "Skipped:", report["skipped_devices"])
    print("Violations:", len(report["violations"]), "Compliant:", len(report["compliant"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))