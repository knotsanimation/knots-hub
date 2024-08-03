import knots_hub.installer

for installer in knots_hub.installer.SUPPORTED_INSTALLERS.values():

    documentation = [
        installer.name(),
        "_" * len(installer.name()),
        "",
    ]
    documentation += installer.documentation()
    print("\n".join(documentation))
