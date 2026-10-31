"""The project's settings for the kit, read from its `.playbook.toml`.

Every kit script runs from the project's checkout, so the file is found at
`./.playbook.toml`, or wherever PLAYBOOK_CONFIG points. A key the file leaves
out takes the default below. The repository comes from `project.repo`, else
GITHUB_REPOSITORY (set in every Actions job).

    import playbook_config as pc
    cfg = pc.load()
    owner, repo = pc.owner_repo(cfg)

See kit/example.playbook.toml for every key, with what it does.
"""
import copy
import os

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

DEFAULTS = {
    "project": {
        "repo": "",
        # The owner's GitHub login (their own comments answer decisions) and
        # the name the pages call them by.
        "owner_login": "",
        "owner_name": "the owner",
        # The owner's day, as a fixed offset from UTC (Windows runners'
        # Python has no time-zone database).
        "utc_offset_hours": 0,
        # The playbook repo the kit is read from (pc_queue reads main's copy).
        "playbook_repo": "zcross00/tbtwd-playbook",
    },
    "board": {
        # The owner's user Project (v2) the sync writes to.
        "project": "",
        "lookback_days": 14,
        "iteration_fields": ["Day", "Week"],
        # `area:` label -> the Team field's option.
        "teams": {},
    },
    "milestones": {
        # The workflow whose scheduled runs on main are the nightly check.
        "nightly_workflow": "ci.yml",
        # Thousands of output tokens a milestone thread burns a day, until a
        # milestone has a day of its own history.
        "planned_rate": 150,
    },
    # A PR's paperwork (board/paperwork.py): the comment that marks an
    # issue groomed, the labels that skip grooming, and the label of the
    # issue a loosened gate must name.
    "paperwork": {"groomed": "groomed: approved",
                  "exempt_labels": ["verification", "deferred gate"],
                  "deferred_label": "deferred gate"},
    "forecast": {"days": 3, "min_signal": 100, "unestimated": 60, "playtest_days": 1,
                 "closed_lookback": 14},
    "wiki": {
        "title": "",
        "tagline": "",
        # The banner (banner.svg) and screenshots (gallery.json, shots/).
        "art_dir": "docs/wiki-art",
        # A file with a "## The one-sentence pitch" section and "### N. Priority" headings.
        "vision": "docs/VISION.md",
        # [wiki page name, repo file] for each page copied from the repo.
        "hand_pages": [["Development-process", "docs/DEVELOPMENT-PROCESS.md"]],
        "reviewed_too": ["docs/VISION.md"],
        "review_days": 30,
        "pending_days": 3,
        # The label on issues waiting on the owner, besides `decision`.
        "needs_owner_label": "needs owner",
    },
    "queue": {
        "ci_workflow": "ci.yml",
        # The branch Code review builds merge trains on; a PR from it with a
        # "Train:" line is a train without the label.
        "train_branch": "",
        # Hosted overflow (#1124): dollars a run, and the month's spend no run
        # goes hosted past.
        "cost": {"overflow": 5.0},
        "overflow_under": 0.0,
    },
    "hosted": {
        "budget": 0.0,
        "warn": 0.0,
        "stop": 0.0,
        # [workflow file, event or ""] for each workflow that runs on GitHub's machines.
        "workflows": [],
    },
    "ci": {
        # Paths (an extended regex) a PR may touch and still skip the build.
        "docs_only": r"^docs/|\.md$",
        # What a conflicted PR is told to run before pushing again.
        "local_check": "the full local check",
    },
    "releases": {
        "tag_pattern": r"^m(\d+)-playtest-(\d+)$",
        # Tags from before the pattern, and the milestone each belongs to.
        "old_tags": {},
    },
    "replay": {
        "check_paths": [],
        "check_lists": [],
        "code_lists": [],
        "save_paths": [],
    },
}


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and out[k]:
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def path():
    return os.environ.get("PLAYBOOK_CONFIG") or ".playbook.toml"


def load(file=None):
    """The settings: the project's file over DEFAULTS. A missing file gives
    the defaults; a file that exists but can't be read is an error."""
    file = file or path()
    data = {}
    if os.path.exists(file):
        if tomllib is None:
            raise RuntimeError("reading .playbook.toml needs Python 3.11 or newer")
        with open(file, "rb") as f:
            data = tomllib.load(f)
    cfg = _merge(DEFAULTS, data)
    if not cfg["project"]["repo"]:
        cfg["project"]["repo"] = os.environ.get("GITHUB_REPOSITORY", "")
    return cfg


def owner_repo(cfg):
    repo = cfg["project"]["repo"]
    if "/" not in repo:
        raise SystemExit("no repository: set project.repo in .playbook.toml, or GITHUB_REPOSITORY")
    return tuple(repo.split("/", 1))


def get(cfg, dotted):
    node = cfg
    for part in dotted.split("."):
        node = node[part]
    return node


if __name__ == "__main__":
    # `python3 kit/lib/playbook_config.py ci.docs_only` prints one setting,
    # for the kit's shell scripts.
    import sys

    value = get(load(), sys.argv[1])
    # No newline: Windows' Python would end the line with \r, which the
    # shell's $(...) keeps.
    sys.stdout.write(value if isinstance(value, str) else __import__("json").dumps(value))
