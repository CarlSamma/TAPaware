from pathlib import Path

p = Path("d:/PROGETTI/Framework-studio/framework/tests/integration/test_hydra_chronos_handoff.py")
text = p.read_text()

text = text.replace(
    "extraction = ExtractionInput.model_validate(input_wrapper[\"extraction_input\"])",
    "extraction = ExtractionInput.model_validate(input_wrapper.extraction_input)",
)
p.write_text(text)
print("FIXED")
