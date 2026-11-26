"""check_md_links.py の検査。期待するアンカー名は GitHub の描画に合わせた。

    python -X utf8 -m unittest discover -s tools/ci -p "test_*.py"
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

import check_md_links as c


def slugs(text):
    return c.heading_slugs(c.prose_lines(text))


def dests(text):
    return [dest for _, dest in c.links(text)]


class SlugTest(unittest.TestCase):
    def test_japanese_and_punctuation(self):
        self.assertEqual(slugs("## 作り（線路・道路）の「X」、 8.2 節"), ["作り線路道路のx-82-節"])
        self.assertEqual(slugs("### `ami_dat.py` と **太字** ①"), ["ami_datpy-と-太字-"])
        self.assertEqual(slugs("# a [link](x.md) <br> _em_ snake_case ##"), ["a-link--em-snake_case"])

    def test_duplicates(self):
        self.assertEqual(slugs("# a\n## a\n# a-1\n# a\n"), ["a", "a-1", "a-1-1", "a-2"])

    def test_skips_code_comment_and_front_matter(self):
        text = "---\nname: x\n---\n```sh\n# no\n```\n<!--\n# no\n-->\n~~~\n```\n# no\n~~~\n# yes\n"
        self.assertEqual(slugs(text), ["yes"])

    def test_setext(self):
        self.assertEqual(slugs("title\n===\n\n- item\n---\n"), ["title"])


class LinkTest(unittest.TestCase):
    def test_forms(self):
        text = '[a](x.md) ![b](<y z.png> "t") [![c](i.png)](p(1).md)\n[r]: ref.md\n<img src="h.png">\n'
        self.assertEqual(dests(text), ["x.md", "y z.png", "i.png", "p(1).md", "ref.md", "h.png"])

    def test_skips_code(self):
        text = "`[a](no.md)`\n```\n[b](no.md)\n```\n| ` |\n| [c](yes.md) ` |\n"
        self.assertEqual(c.links(text), [(6, "yes.md")])


class CheckTest(unittest.TestCase):
    def run_check(self, tree):
        with tempfile.TemporaryDirectory() as d:
            for name, text in tree.items():
                path = Path(d, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return c.check(Path(d), set(tree))

    def test_ok(self):
        sources, count, errors = self.run_check(
            {
                "addons/x/README.md": "# 見出し\n[a](#見出し) [b](docs/a.md#%E7%AF%80) [c](docs) [d](../../docs/r.md#id)\n"
                "[e](https://example.com/#no) [f](a.py#L3) [g](docs/a.md?plain=1#L1)\n",
                "addons/x/a.py": "",
                "addons/x/docs/a.md": "## 節\r\n",
                "docs/r.md": '<a id="id"></a>\n',
                ".claude/worktrees/w/addons/y/README.md": "[x](no.md)\n",
            }
        )
        self.assertEqual((sources, count, errors), (3, 6, []))

    def test_broken(self):
        _, _, errors = self.run_check(
            {
                ".claude/skills/s/SKILL.md": "[a](no.md)\n[b](#no)\n[c](A.md)\n[d](a.md#no)\n[e](/x)\n"
                "[f](../../../../x)\n[g](a.md/)\n",
                ".claude/skills/s/a.md": "# a\n",
            }
        )
        self.assertEqual(
            [tuple(e.split(": ")[:2]) for e in errors],
            [
                (f".claude/skills/s/SKILL.md:{line}", reason)
                for line, reason in enumerate(
                    [
                        "リンク先が無い",
                        "アンカーが無い",
                        "リンク先が無い",
                        "アンカーが無い",
                        "絶対パスのリンクは使わない",
                        "リポジトリの外を指す",
                        "リンク先が無い",
                    ],
                    1,
                )
            ],
        )

    def test_inside_a_worktree(self):
        # root の途中に .claude/worktrees があっても飛ばさない（#304 の空振り）
        with tempfile.TemporaryDirectory() as d:
            root = Path(d, ".claude", "worktrees", "w")
            (root / "addons").mkdir(parents=True)
            (root / "addons" / "a.md").write_text("[x](no.md)\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            sources, _, errors = c.check(root, c.repo_files(root))
        self.assertEqual((sources, len(errors)), (1, 1))


if __name__ == "__main__":
    unittest.main()
