import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comments  # noqa: E402


def lines(path, src):
    return [first for first, _, _ in comments.comments_in(path, src)]


class RustTest(unittest.TestCase):
    def test_line_doc_and_inner_doc_comments_are_found(self):
        src = '//! module\n/// item\nfn a() {} // trailing\n'
        self.assertEqual(lines('a.rs', src), [1, 2, 3])

    def test_nested_block_comment_is_one_comment(self):
        src = 'fn a() {}\n/* outer /* inner */ still */\nfn b() {}\n'
        self.assertEqual(lines('a.rs', src), [2])

    def test_slashes_inside_strings_are_not_comments(self):
        src = 'let u = "http://x";\nlet r = r#"// not "a" comment"#;\nlet b = b"//";\n'
        self.assertEqual(lines('a.rs', src), [])

    def test_lifetimes_and_char_literals_do_not_open_strings(self):
        src = "fn a<'a>(x: &'a str) -> char { '\"' }\n// real\nlet q = '\\'';\n"
        self.assertEqual(lines('a.rs', src), [2])

    def test_attributes_are_code(self):
        src = '#![allow(dead_code)]\n#[allow(clippy::too_many_arguments)]\nfn a() {}\n'
        self.assertEqual(lines('a.rs', src), [])

    def test_line_count_survives_multiline_strings(self):
        src = 'let s = "one\ntwo\nthree";\n// here\n'
        self.assertEqual(lines('a.rs', src), [4])


class ScriptTest(unittest.TestCase):
    def test_eslint_directive_is_allowed_but_prose_after_it_is_not(self):
        src = '// eslint-disable-next-line no-console\nconsole.log(1)\n// eslint-disable-next-line no-console because\n'
        self.assertEqual(lines('a.js', src), [3])

    def test_template_literal_hides_slashes(self):
        self.assertEqual(lines('a.ts', 'const a = `//x`;\n'), [])

    def test_csharp_verbatim_string(self):
        self.assertEqual(lines('a.cs', 'var p = @"C:\\x\\";\n// c\n'), [2])


class PythonTest(unittest.TestCase):
    def test_comments_docstrings_and_bare_strings_are_found(self):
        src = '"""module"""\nimport os  # why\n\ndef f():\n    """doc"""\n    "loose"\n    return "# no"\n'
        self.assertEqual(lines('a.py', src), [1, 2, 5, 6])

    def test_shebang_encoding_and_directives_are_allowed(self):
        src = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport x  # noqa: E402\ny = 1  # type: ignore\n'
        self.assertEqual(lines('a.py', src), [])

    def test_unparsable_file_is_reported(self):
        self.assertEqual(len(comments.comments_in('a.py', 'def (:\n')), 1)


class HashTest(unittest.TestCase):
    def test_shell_comment_shebang_and_special_hashes(self):
        src = '#!/usr/bin/env bash\n# why\necho "$#" ${#x} a#b # trailing\n'
        self.assertEqual(lines('a.sh', src), [2, 3])

    def test_shell_heredoc_body_is_not_a_comment(self):
        src = "cat <<'EOF'\n# heading\nEOF\n# after\n"
        self.assertEqual(lines('a.sh', src), [4])

    def test_shellcheck_directive_is_allowed(self):
        self.assertEqual(lines('a.sh', '# shellcheck disable=SC2086\nls $x\n'), [])

    def test_yaml_apostrophe_in_plain_scalar_does_not_open_a_string(self):
        src = "name: don't stop # why\nkey: '# not'\n"
        self.assertEqual(lines('a.yml', src), [1])

    def test_toml_comment_and_multiline_string(self):
        src = 'a = "#x" # why\nb = """\n# inside\n"""\n# after\n'
        self.assertEqual(lines('a.toml', src), [1, 5])

    def test_powershell_block_comment(self):
        self.assertEqual(lines('a.ps1', '<#\nhelp\n#>\n$a = 1\n'), [1])


class OtherFilesTest(unittest.TestCase):
    def test_markdown_and_unknown_files_are_out_of_scope(self):
        self.assertEqual(lines('a.md', '<!-- anchor -->\n'), [])
        self.assertEqual(lines('a.png', '//'), [])

    def test_exempt_globs_cover_subdirectories(self):
        self.assertTrue(comments.exempt('data/systems/sol.ron', ['data/systems/*']))
        self.assertFalse(comments.exempt('data/hulls.ron', ['data/systems/*']))


class DiffTest(unittest.TestCase):
    def test_only_comments_on_added_lines_count(self):
        with tempfile.TemporaryDirectory() as repo:
            def run(*args):
                subprocess.run(args, cwd=repo, check=True, capture_output=True)
            run('git', 'init', '-q', '-b', 'main')
            run('git', 'config', 'user.email', 'a@b')
            run('git', 'config', 'user.name', 'a')
            with open(os.path.join(repo, 'a.rs'), 'w') as f:
                f.write('// old\nfn a() {}\n')
            run('git', 'add', '.')
            run('git', 'commit', '-qm', 'base')
            with open(os.path.join(repo, 'a.rs'), 'w') as f:
                f.write('// old\nfn a() {}\n// new\nfn b() {}\n')
            here = os.getcwd()
            os.chdir(repo)
            try:
                added = comments.added_lines('main')
                report = comments.scan(['a.rs'], [], added)
            finally:
                os.chdir(here)
            self.assertEqual([(p, n) for p, n, _ in report], [('a.rs', 3)])


if __name__ == '__main__':
    unittest.main()
