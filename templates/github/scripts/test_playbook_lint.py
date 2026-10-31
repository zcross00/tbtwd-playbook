import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from playbook_lint import check

assert check("Refs #12\n- ask: test_x", "", False) == []
assert check("Docs tweak", "", True) == []
assert len(check("Closes #12", "", True)) == 1
assert len(check("Refs #3", "fix: #44 broke", False)) == 1
assert len(check("Refs #3", "Resolved owner/repo#9", False)) == 1
assert check("Refs #3\nthe fix in #44", "fix the parser", False) == []
assert len(check("Some code change", "", False)) == 1
print("ok")
