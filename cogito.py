#!/usr/bin/env python3
import os
from pathlib import Path
from openai import OpenAI

INSTRUCTIONS_PATH = "/prompts/v1.txt"
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"   # default: dry-run on
NAME_CONTAINS = os.getenv("NAME_CONTAINS", "").strip()  # optional filter
CONFIRM = "YES"  # must equal "YES" to actually update when DRY_RUN=0

def read_instructions() -> str:
    if not INSTRUCTIONS_PATH.exists():
        raise FileNotFoundError(f"Missing {INSTRUCTIONS_PATH.resolve()}")
    text = INSTRUCTIONS_PATH.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("instructions.txt is empty")
    return text

def assistant_matches(a) -> bool:
    if not NAME_CONTAINS:
        return True
    name = (a.name or "")
    return NAME_CONTAINS.lower() in name.lower()

def main() -> None:
    client = OpenAI()
    new_instructions = read_instructions()
    if not DRY_RUN and CONFIRM != "YES":
        raise SystemExit('Refusing to update: set CONFIRM=YES and DRY_RUN=0 to proceed.')
    updated = 0
    considered = 0
    # List assistants (paginated). The API supports listing assistants. :contentReference[oaicite:2]{index=2}
    page = client.beta.assistants.list(limit=100)
    while True:
        for a in page.data:
            if not assistant_matches(a):
                continue
            considered += 1
            print(f"- {a.id} | name={a.name!r}")
            if DRY_RUN:
                continue
            client.beta.assistants.update(
                assistant_id=a.id,
                instructions=new_instructions,
            )
            updated += 1

        if not getattr(page, "has_next_page", False):
            break
        page = page.get_next_page()

    print("\nSummary")
    print(f"Considered: {considered}")
    print(f"Updated:    {updated} {'(dry-run)' if DRY_RUN else ''}")

if __name__ == "__main__":
    main()
