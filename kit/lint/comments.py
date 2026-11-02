import argparse
import ast
import fnmatch
import io
import os
import re
import subprocess
import sys
import tokenize

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import playbook_config  # noqa: E402

SLASH_LANGUAGES = {
    '.rs': 'rust', '.ron': 'rust', '.wgsl': 'rust',
    '.js': 'script', '.mjs': 'script', '.ts': 'script', '.tsx': 'script', '.jsx': 'script',
    '.cs': 'csharp', '.java': 'c', '.kt': 'c', '.go': 'c', '.c': 'c', '.h': 'c',
    '.cpp': 'c', '.hpp': 'c', '.swift': 'c', '.jsonc': 'c',
}
HASH_LANGUAGES = {
    '.sh': 'shell', '.bash': 'shell', '.yml': 'yaml', '.yaml': 'yaml',
    '.toml': 'toml', '.ps1': 'powershell', '.psm1': 'powershell',
}
PYTHON = {'.py'}

DIRECTIVES = {
    'python': [r'noqa(: ?[A-Z]+[0-9]+(, ?[A-Z]+[0-9]+)*)?', r'type: ?ignore(\[[\w, -]+\])?',
               r'pragma: no (cover|branch)', r'fmt: ?(on|off|skip)'],
    'shell': [r'shellcheck (disable|enable|source|shell)=\S+'],
    'yaml': [r'yaml-language-server: \$schema=\S+'],
    'powershell': [r'requires -\w+.*'],
    'script': [r'eslint-disable(-next-line|-line)?( [\w/@-]+(, ?[\w/@-]+)*)?',
               r'eslint-enable( [\w/@-]+(, ?[\w/@-]+)*)?',
               r'@ts-(ignore|expect-error|nocheck)', r'/ ?<reference [^>]*/>'],
}
ENCODING = re.compile(r'-\*- coding[:=] ?[\w.-]+ ?-\*-|coding[:=] ?[\w.-]+')


def directive(language, text):
    body = text.strip()
    return any(re.fullmatch(p, body, re.IGNORECASE) for p in DIRECTIVES.get(language, []))


def raw_string_end(src, i):
    j = i
    if src[j] == 'b':
        j += 1
    if j >= len(src) or src[j] != 'r':
        return None
    j += 1
    hashes = 0
    while j < len(src) and src[j] == '#':
        hashes += 1
        j += 1
    if j >= len(src) or src[j] != '"':
        return None
    close = '"' + '#' * hashes
    end = src.find(close, j + 1)
    return len(src) if end < 0 else end + len(close)


def quoted_end(src, i, quote, escapes=True):
    j = i + 1
    while j < len(src):
        if escapes and src[j] == '\\':
            j += 2
            continue
        if src[j] == quote:
            if not escapes and src[j + 1:j + 2] == quote:
                j += 2
                continue
            return j + 1
        j += 1
    return len(src)


def rust_char_end(src, i):
    if src[i + 1:i + 2] == '\\':
        end = src.find("'", i + 2)
        return None if end < 0 else end + 1
    if i + 2 < len(src) and src[i + 2] == "'" and src[i + 1] != "'":
        return i + 3
    return None


def slash_comments(src, language):
    found = []
    line = 1
    i = 0
    n = len(src)
    word = re.compile(r'[A-Za-z0-9_]')
    while i < n:
        c = src[i]
        if c == '\n':
            line += 1
            i += 1
            continue
        if src.startswith('//', i):
            end = src.find('\n', i)
            end = n if end < 0 else end
            text = src[i + 2:end]
            if not directive(language, text):
                found.append((line, line, src[i:end].strip()))
            i = end
            continue
        if src.startswith('/*', i):
            depth = 1
            j = i + 2
            while j < n and depth:
                if language == 'rust' and src.startswith('/*', j):
                    depth += 1
                    j += 2
                elif src.startswith('*/', j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            text = src[i:j]
            last = line + text.count('\n')
            if not directive(language, text[2:-2]):
                found.append((line, last, text.split('\n')[0].strip()))
            line = last
            i = j
            continue
        if language == 'rust' and c in 'br' and (i == 0 or not word.match(src[i - 1])):
            end = raw_string_end(src, i)
            if end is not None:
                line += src.count('\n', i, end)
                i = end
                continue
        if language == 'csharp' and c == '@' and src[i + 1:i + 2] == '"':
            end = quoted_end(src, i + 1, '"', escapes=False)
            line += src.count('\n', i, end)
            i = end
            continue
        if c == '"' or (c == '`' and language == 'script'):
            end = quoted_end(src, i, c)
            line += src.count('\n', i, end)
            i = end
            continue
        if c == "'":
            if language == 'rust':
                end = rust_char_end(src, i)
                if end is None:
                    i += 1
                    continue
            else:
                end = quoted_end(src, i, "'")
            line += src.count('\n', i, end)
            i = end
            continue
        i += 1
    return found


HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
QUOTE_OPENERS = ' \t[{,:=('


def hash_comments(src, language):
    found = []
    lines = src.split('\n')
    quote = None
    heredoc = None
    block = False
    for number, text in enumerate(lines, 1):
        if heredoc:
            if text.strip() == heredoc:
                heredoc = None
            continue
        if number == 1 and text.startswith('#!'):
            continue
        if language == 'powershell' and block:
            if '#>' in text:
                block = False
            continue
        i = 0
        while i < len(text):
            c = text[i]
            if quote:
                if language == 'toml' and quote in ('"""', "'''"):
                    if text.startswith(quote, i):
                        quote = None
                        i += 3
                        continue
                elif c == '\\' and quote == '"':
                    i += 2
                    continue
                elif c == quote:
                    quote = None
                i += 1
                continue
            if language == 'toml' and text.startswith(('"""', "'''"), i):
                quote = text[i:i + 3]
                i += 3
                continue
            if c in '"\'':
                if language != 'yaml' or i == 0 or text[i - 1] in QUOTE_OPENERS:
                    quote = c
                i += 1
                continue
            if language == 'powershell' and text.startswith('<#', i):
                found.append((number, number, text[i:].strip()))
                if '#>' not in text[i:]:
                    block = True
                break
            if c == '#' and (language == 'toml' or i == 0 or text[i - 1] in ' \t;'):
                if not directive(language, text[i + 1:]):
                    found.append((number, number, text[i:].strip()))
                break
            i += 1
        if language == 'yaml' or language == 'toml' and quote not in ('"""', "'''"):
            quote = None
        if language == 'shell' and not quote:
            match = HEREDOC.search(text)
            if match:
                heredoc = match.group(2)
    return found


def python_comments(src):
    found = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(src).readline):
            if token.type != tokenize.COMMENT:
                continue
            row = token.start[0]
            text = token.string
            if row == 1 and text.startswith('#!'):
                continue
            if row <= 2 and ENCODING.search(text):
                continue
            if directive('python', text[1:]):
                continue
            found.append((row, row, text.strip()))
        tree = ast.parse(src)
    except (tokenize.TokenError, SyntaxError) as error:
        return [(getattr(error, 'lineno', 1) or 1, 1, f'cannot parse: {error}')]
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            first = node.value.value.strip().split('\n')[0]
            found.append((node.lineno, node.end_lineno, f'"""{first[:60]}'))
    return sorted(found)


def language_of(path):
    extension = os.path.splitext(path)[1].lower()
    if extension in PYTHON:
        return 'python'
    return SLASH_LANGUAGES.get(extension) or HASH_LANGUAGES.get(extension)


def comments_in(path, src):
    language = language_of(path)
    if language is None:
        return []
    if language == 'python':
        return python_comments(src)
    if os.path.splitext(path)[1].lower() in SLASH_LANGUAGES:
        return slash_comments(src, language)
    return hash_comments(src, language)


def exempt(path, patterns):
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout


def added_lines(base):
    merge_base = git('merge-base', base, 'HEAD').strip()
    diff = git('diff', '--unified=0', '--no-color', '--diff-filter=AM', merge_base)
    added = {}
    current = None
    for row in diff.split('\n'):
        if row.startswith('+++ '):
            current = row[6:] if row.startswith('+++ b/') else None
            if current:
                added.setdefault(current, set())
        elif row.startswith('@@') and current:
            match = re.search(r'\+(\d+)(?:,(\d+))?', row)
            start = int(match.group(1))
            count = 1 if match.group(2) is None else int(match.group(2))
            added[current].update(range(start, start + count))
    return added


def tracked(paths):
    return [p for p in git('ls-files', '--', *paths).split('\n') if p]


def scan(files, patterns, added=None):
    report = []
    for path in files:
        if exempt(path, patterns) or language_of(path) is None or not os.path.isfile(path):
            continue
        with open(path, encoding='utf-8', errors='replace') as handle:
            src = handle.read()
        for first, last, text in comments_in(path, src):
            if added is not None and not added.get(path, set()) & set(range(first, last + 1)):
                continue
            report.append((path, first, text))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Lists code comments, which the standards ban.')
    parser.add_argument('paths', nargs='*', help='files or directories; all tracked files when none')
    parser.add_argument('--diff', metavar='BASE', help='only comments on lines added since BASE')
    parser.add_argument('--count', action='store_true', help='comment count per file, largest first')
    args = parser.parse_args(argv)
    patterns = playbook_config.load()['comments']['exempt']
    if args.diff:
        added = added_lines(args.diff)
        files = sorted(p for p in added if not args.paths or any(
            p == a or p.startswith(a.rstrip('/') + '/') for a in args.paths))
        report = scan(files, patterns, added)
    else:
        report = scan(tracked(args.paths), patterns)
    if args.count:
        counts = {}
        for path, _, _ in report:
            counts[path] = counts.get(path, 0) + 1
        for path, total in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f'{total:6} {path}')
        print(f'{len(report):6} total in {len(counts)} files')
    else:
        for path, line, text in report:
            print(f'{path}:{line}: {text[:100]}')
        if report:
            print(f'{len(report)} comments; the standards ban them (standards/general.md, section 4)',
                  file=sys.stderr)
    return 1 if report else 0


if __name__ == '__main__':
    sys.exit(main())
