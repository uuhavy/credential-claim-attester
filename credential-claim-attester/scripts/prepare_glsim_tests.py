"""Repair glsim 0.29.2 schema discovery for gltest's calldata proxy.

The execution instance stays wrapped; only schema/class caching uses the real
storage class. No contract, mock response, vote or assertion is changed.
"""
import importlib.metadata
from pathlib import Path
import glsim.engine

assert importlib.metadata.version("genlayer-test") == "0.29.2"
path = Path(glsim.engine.__file__)
source = path.read_text(encoding="utf-8")
old = "        contract_cls = type(instance)\n        for cls in type(instance).__mro__:\n"
new = (
    "        # Discover storage class behind the calldata proxy.\n"
    "        schema_instance = getattr(instance, '_instance', instance)\n"
    "        contract_cls = type(schema_instance)\n"
    "        for cls in type(schema_instance).__mro__:\n"
)
if new in source:
    print("glsim schema/class-cache compatibility patch already installed.")
else:
    assert source.count(old) == 1
    path.write_text(source.replace(old, new), encoding="utf-8")
    print("Applied glsim schema/class-cache compatibility patch.")
