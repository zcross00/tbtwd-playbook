"""Daily backlog review helper (playbook/09-cadences.md, "Daily backlog review").

Usage, from the project's checkout (it reads .playbook.toml there):
  python3 kit/review/scan.py OUTDIR            pick and print the day's review
  python3 kit/review/scan.py --record OUTDIR   after the run, stamp the picked issues

REVIEW_STAMPS names the JSON file of last review dates (default
./last-reviewed.json); keep it outside the repo, so a review fires no workflow.

Picks, in this order:
  1. up to 50 non-parked open issues, least recently reviewed first (last-reviewed.json, then updated_at);
  2. every issue whose newest board status is In review for more than 24 hours;
  3. every open decision issue (label `decision` or wiki.needs_owner_label);
  4. every open milestone past its 50% date (from the "50% Mon D" in its description).
Nothing is posted on the issues: the last review date lives in REVIEW_STAMPS,
so a review doesn't fire the board workflows. Read only what a flag points at. Needs the container's gh.
"""
import datetime as dt, json, os, re, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import playbook_config  # noqa: E402

CFG = playbook_config.load()
R = 'repos/' + '/'.join(playbook_config.owner_repo(CFG))
OWNER_NAME = CFG['project']['owner_name']
NEEDS_OWNER = CFG['wiki']['needs_owner_label']
STAMPS = os.environ.get('REVIEW_STAMPS') or 'last-reviewed.json'
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.date().isoformat()

def api(path):
    return json.loads(subprocess.run(['gh', 'api', f'{R}/{path}'], capture_output=True, text=True, check=True).stdout)

def load_stamps():
    try:
        return json.load(open(STAMPS))
    except (OSError, ValueError):
        return {}

if sys.argv[1] == '--record':
    out = sys.argv[2]
    stamps = load_stamps()
    picked = json.load(open(f'{out}/picked.json'))
    for n in picked:
        stamps[str(n)] = TODAY
    json.dump(stamps, open(STAMPS, 'w'), indent=0, sort_keys=True)
    print(f'stamped {len(picked)} issues {TODAY}')
    sys.exit()

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
stamps = load_stamps()

issues = []
for page in range(1, 10):
    batch = api(f'issues?state=open&per_page=100&page={page}')
    issues += [i for i in batch if 'pull_request' not in i]
    if len(batch) < 100:
        break
labels = lambda i: {l['name'] for l in i['labels']}
i_body = {i['number']: i['body'] or '' for i in issues}
milestones = api('milestones?state=open&per_page=100')
due = {m['number']: (m['due_on'] or '-')[:10] for m in milestones}

nonparked = [i for i in issues if 'parked' not in labels(i)]
nonparked.sort(key=lambda i: (stamps.get(str(i['number']), ''), i['updated_at']))
picked = nonparked[:50]
json.dump([i['number'] for i in picked], open(f'{out}/picked.json', 'w'))
json.dump(picked, open(f'{out}/list.json', 'w'))

def board_of(n):
    c = api(f'issues/{n}/comments?per_page=100')
    json.dump(c, open(f'{out}/c{n}.json', 'w'))
    board, status_at = {}, None
    for body, at in [(i_body[n], None)] + [(x['body'], x['created_at']) for x in c]:
        for m in re.finditer(r'board:\**([^\n]*)', body or ''):
            for k, v in re.findall(r'(\w+)=(\S+(?: review| progress)?)', m.group(1)):
                board[k] = v
                if k == 'status':
                    status_at = at
    return board, status_at, c

print('== 1. non-parked, least recently reviewed (reviewed / updated / ms due / status est day / flags | title)')
in_review = []
for i in nonparked:
    n = i['number']
    board, status_at, c = board_of(n)
    st = board.get('status', '-')
    if st.startswith('In review') and status_at and NOW - dt.datetime.fromisoformat(status_at.replace('Z', '+00:00')) > dt.timedelta(hours=24):
        in_review.append((n, status_at[:16], i['title'][:70]))
    if i not in picked:
        continue
    text = i_body[n] + '\n'.join(x['body'] for x in c)
    ms = i['milestone']['number'] if i['milestone'] else None
    d = due.get(ms, '-')
    flags = []
    if not ms: flags.append('NO-MILESTONE')
    if not re.search(r'\*\*Check:?\*\*|Check:|[Dd]one[- ]when', text): flags.append('NO-CHECK')
    if 'estimate' not in board: flags.append('NO-EST')
    if 'day' not in board: flags.append('NO-DAY')
    elif d != '-' and board['day'] > d: flags.append(f'DAY>DUE{d}')
    if not re.search(r'cmsg_|' + re.escape(OWNER_NAME) + r'[^\n]{0,40}"', text): flags.append('NO-OWNER-WORDS')
    if ms and 'groomed' not in text and 'verification' not in labels(i): flags.append('NOT-GROOMED')
    if re.search(r'once [^)\n]{0,30}merges', i_body[n]): flags.append('STALE-ONCE-MERGES')
    if 'blob/claude/' in i_body[n]: flags.append('BRANCH-LINK')
    if st.startswith('In review') and 'deferred gate' in labels(i): flags.append('DEFERRED-IN-REVIEW')
    print(n, stamps.get(str(n), 'never'), i['updated_at'][:10], f'm{ms or "-"} {d}', st, board.get('estimate', '-'), board.get('day', '-'),
          ' '.join(flags) or '-', '|', i['title'][:70], sep='\t')

print('\n== 2. In review for more than 24h (since)')
for row in sorted(in_review, key=lambda r: r[1]):
    print(*row, sep='\t')

print('\n== 3. open decision issues')
for i in issues:
    if labels(i) & {'decision', NEEDS_OWNER}:
        print(i['number'], i['updated_at'][:10], i['title'][:80], sep='\t')

print('\n== 4. milestones past their 50% date')
MON = {m: k for k, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
for m in milestones:
    desc = m['description'] or ''
    hit = re.search(r'Forecast dates[^\n]*?50% (\w{3}) (\d{1,2})', desc) or re.search(r'50% (\w{3}) (\d{1,2})', desc)
    if not hit or hit.group(1) not in MON:
        print(m['number'], 'NO-50%-DATE', m['title'][:70], sep='\t')
        continue
    half = dt.date(NOW.year, MON[hit.group(1)], int(hit.group(2)))
    if half < NOW.date():
        print(m['number'], f'50% {half}', f'due {due[m["number"]]}', f'{m["open_issues"]} open', m['title'][:60], sep='\t')
