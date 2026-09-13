import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from prompts import REACT_AGENT_SYSTEM_PROMPT


class AgentPromptTest(unittest.TestCase):
    def test_report_requests_require_tool_validation(self):
        self.assertIn(
            "Không tự kết luận mã không tồn tại",
            REACT_AGENT_SYSTEM_PROMPT,
        )
        self.assertIn(
            "phải dùng Observation của tool để xác minh",
            REACT_AGENT_SYSTEM_PROMPT,
        )


if __name__ == "__main__":
    unittest.main()
