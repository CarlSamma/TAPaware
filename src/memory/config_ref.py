# Re-export config from parent package
import sys
from pathlib import Path

# Ensure parent src/ is on path for absolute imports
_src = str(Path(__file__).parent.parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from config import AwareConfig  # noqa: E402, F401
