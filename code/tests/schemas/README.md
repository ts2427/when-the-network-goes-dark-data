# Test schemas

`zenodo_legacyrecord.json`: "Zenodo Legacy Deposit Schema v1.0.0" (JSON Schema draft 4), downloaded 2026-11-25 from
https://raw.githubusercontent.com/zenodo/zenodo/master/zenodo/modules/deposit/jsonschemas/deposits/records/legacyrecord.json
(SHA-256 e275ddb915367510c4809db54b672fdd1fd31d133b55d9509eb2460022073562). Unmodified.

`tests/test_zenodo_json.py` validates `.zenodo.json` against it with one addition: a `version` string. The legacy
schema has no `version` property and forbids unknown ones, but Zenodo's own `.zenodo.json` documentation
(https://help.zenodo.org/docs/github/describe-software/zenodo-json/, read 2026-11-25) includes `version` in its
example, and a GitHub release sets it.
