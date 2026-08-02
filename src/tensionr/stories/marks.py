"""The three states a source can be in about an actor.

Their own module, with no imports, for two reasons. They are the project's most
load-bearing vocabulary — presence, absence, and *not evaluable*, where the third is
never a missing value (#22) — so they are defined once and nothing restates them. And
the page generator needs them without needing the pipeline: keeping them here means
rendering a page costs no third-party dependency, so the site assembly can run each
branch's own generator with nothing but a Python interpreter.
"""

PRESENT = "present"
ABSENT = "absent"
UNRESOLVED = "unresolved"
