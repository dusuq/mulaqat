import json
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


class PackageTest(unittest.TestCase):
    def test_versions_agree(self):
        plugin = json.loads(read(".claude-plugin", "plugin.json"))
        market = json.loads(read(".claude-plugin", "marketplace.json"))
        self.assertEqual(plugin["version"], market["plugins"][0]["version"])
        self.assertIn(f"## [{plugin['version']}]", read("CHANGELOG.md"))

    def test_skill_frontmatter(self):
        text = read("skills", "mulaqat", "SKILL.md")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md needs YAML frontmatter")
        front = match.group(1)
        self.assertRegex(front, r"(?m)^name: mulaqat$")
        description = re.search(r"(?m)^description: (.+)$", front).group(1)
        self.assertLessEqual(len(description), 1024)
        self.assertNotIn("<", description)

    def test_referenced_files_exist(self):
        text = read("skills", "mulaqat", "SKILL.md")
        for ref in set(re.findall(r"`((?:references|scripts)/[\w.-]+)`", text)):
            self.assertTrue(
                os.path.exists(os.path.join(ROOT, "skills", "mulaqat", ref)),
                f"missing {ref}",
            )


if __name__ == "__main__":
    unittest.main()
