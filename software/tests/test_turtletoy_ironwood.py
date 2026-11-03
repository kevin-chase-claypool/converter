"""Execute the checked-in Turtletoy creation with a local API-compatible mock."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKETCH = ROOT / "samples" / "turtletoy" / "ironwood.js"
RENDERER = ROOT / "tools" / "render_turtletoy.js"


class TurtletoyIronwoodTests(unittest.TestCase):
    def test_sketch_is_self_contained_and_executes_through_turtle_walk(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is not installed")

        source = SKETCH.read_text(encoding="utf-8")
        self.assertIn("Canvas.setpenopacity(1)", source)
        self.assertIn("function walk(i)", source)
        self.assertNotIn("require(", source)
        self.assertNotIn("import ", source)

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "ironwood.svg"
            result = subprocess.run(
                [node, str(RENDERER), str(SKETCH), str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            stats = json.loads(result.stdout)

        self.assertEqual(stats["strokes"], 272)
        self.assertGreater(stats["points"], 1500)
        min_x, min_y, max_x, max_y = stats["bounds"]
        self.assertGreaterEqual(min(min_x, min_y), -100.0)
        self.assertLessEqual(max(max_x, max_y), 100.0)


if __name__ == "__main__":
    unittest.main()
