import json
from pathlib import Path
from typing import List, Dict, Any

class PersonaDatabase:
    """
    A lightweight class to load and manage persona data
    from a JSON file for use in your focus-group simulation app.
    """

    def __init__(self, json_path: str = "personas.json"):
        self.json_path = Path(json_path)
        self.personas = self._load_personas()

    def _load_personas(self) -> List[Dict[str, Any]]:
        """Load personas from a JSON file."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Persona file not found at {self.json_path}")
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all personas."""
        return self.personas

    def get_by_id(self, persona_id: int) -> Dict[str, Any]:
        """Return a persona by ID."""
        for p in self.personas:
            if p["id"] == persona_id:
                return p
        raise ValueError(f"No persona found with id {persona_id}")

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search personas by keyword (matches name, occupation, or traits).
        Case-insensitive.
        """
        keyword = keyword.lower()
        results = []
        for p in self.personas:
            combined_text = f"{p['name']} {p['occupation']} {' '.join(p['interests'])}".lower()
            if keyword in combined_text:
                results.append(p)
        return results

    def summary(self) -> str:
        """Return a brief summary of all personas."""
        summaries = [
            f"{p['id']}. {p['name']} ({p['occupation']} - {p['location']})"
            for p in self.personas
        ]
        return "\n".join(summaries)


if __name__ == "__main__":
    db = PersonaDatabase("personas.json")

    print("✅ Loaded Personas:")
    print(db.summary())

    print("\n🔍 Example Search: 'designer'")
    matches = db.search("designer")
    for m in matches:
        print(f"- {m['name']} ({m['occupation']})")

    print("\n👤 Example Get by ID (3):")
    print(db.get_by_id(3))
