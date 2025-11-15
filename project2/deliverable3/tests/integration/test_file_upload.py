import json
from utils import get_personas

def test_upload_valid_file(tmp_path):
    data = [{"name": "A", "occupation": "X", "tech_proficiency": "High", "behavioral_traits": []}]
    f = tmp_path / "p.json"
    f.write_text(json.dumps(data))

    personas = get_personas(open(f, "r"))
    assert personas[0]["name"] == "A"
