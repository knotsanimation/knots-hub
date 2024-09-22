import dataclasses

import knots_hub.installer
from knots_hub import serializelib


def main():

    for vendor_name, vendor in knots_hub.installer.SUPPORTED_VENDORS.items():

        documentation = [
            vendor_name,
            "_" * len(vendor_name),
            "",
        ]
        documentation += vendor.get_documentation()
        print("\n".join(documentation))


main()
