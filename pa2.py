# Name: Alex Wang  Student ID: 101377606
import sys
import xml.etree.ElementTree as ET


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


def main(args):
    """Run the program and return the exit code."""
    # args[0] is pa2.py, so exactly two arguments means length 3
    if len(args) != 3:
        print("usage: python pa2.py DEVICES.xml POLICY.yaml")
        return 2

    try:
        # read the inventory, a bad file raises my InputFileError
        site, devices, skipped = load_inventory(args[1])
    except InputFileError as error:
        # show the message without a traceback and exit with code 1
        print("Error:", error)
        return 1

    # for now just print the device ids
    for device in devices:
        print(device.dev_id)
    print("Skipped:", skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))