from pathlib import Path

p = Path("d:/PROGETTI/Framework-studio/framework/src/chronos/orchestrator.py")
text = p.read_text()

# Move uuid imports to top-level
if "from uuid import UUID" in text and "from uuid import uuid4" not in text:
    text = text.replace("from uuid import UUID", "from uuid import UUID, uuid4")

# Inline import removal
old_inline = "        from uuid import UUID\n"
if old_inline in text:
    text = text.replace(old_inline, "")

# Simplify attack_id construction
old = "            attack_id=UUID(str(attack_id)) if attack_id else uuid4(),"
new = "            attack_id=UUID(str(attack_id)) if attack_id else uuid4(),  # type: ignore[arg-type]"
if old in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("FIXED")
else:
    print("pattern not found")
