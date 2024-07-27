import dataclasses

import knots_hub

fields = dataclasses.fields(knots_hub.config.HubConfig)

for field in fields:
    print(f"{field.metadata['environ']}")
