import json
from pathlib import Path

import pytest
from openai.types.audio.transcription_verbose import TranscriptionVerbose

from ad_begone.models import SegmentAnnotation

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _discover_fixtures():
    """Find all fixture directories containing transcription.json and ground_truth.json."""
    if not FIXTURES_DIR.is_dir():
        return []
    fixtures = []
    for d in sorted(FIXTURES_DIR.iterdir()):
        if d.is_dir() and (d / "transcription.json").exists() and (d / "ground_truth.json").exists():
            fixtures.append(d)
    return fixtures


def _load_fixture(fixture_dir: Path):
    """Load a fixture directory into (transcription, ground_truth, name)."""
    with open(fixture_dir / "transcription.json", "r") as f:
        transcription = TranscriptionVerbose.model_validate_json(f.read())

    with open(fixture_dir / "ground_truth.json", "r") as f:
        raw = json.load(f)
    ground_truth = [SegmentAnnotation.model_validate(item) for item in raw]

    return transcription, ground_truth, fixture_dir.name


_FIXTURE_DIRS = _discover_fixtures()


@pytest.fixture(params=_FIXTURE_DIRS, ids=[d.name for d in _FIXTURE_DIRS])
def accuracy_fixture(request):
    """Yield (transcription, ground_truth, name) for each fixture directory."""
    return _load_fixture(request.param)
