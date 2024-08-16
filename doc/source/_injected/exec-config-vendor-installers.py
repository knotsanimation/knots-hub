import knots_hub.installer

for (
    installer,
    installer_doc,
) in knots_hub.installer.SUPPORTED_INSTALLERS_DOCUMENTATION.items():

    documentation = [
        installer.name(),
        "_" * len(installer.name()),
        "",
    ]
    documentation += installer_doc
    print("\n".join(documentation))
