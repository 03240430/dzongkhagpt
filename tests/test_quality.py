from core.translator import clean_dzongkha
from core.glossary import normalize, lookup, load_glossary

# 1. Punctuation cleanup
assert clean_dzongkha("ཨིན་ན?") == "ཨིན་ན།", "question mark should become །"
assert clean_dzongkha("ཨིན་ན །") == "ཨིན་ན།", "space before । should go"
assert clean_dzongkha("ཨིན་ན།") == "ཨིན་ན།", "already correct text must not change"
print("OK  punctuation cleanup")

# 2. Glossary text matching
assert normalize("  Hello!!  ") == "hello"
assert normalize("Thank   You.") == "thank you"
print("OK  glossary normalize")

# 3. Glossary file
en_to_dz, dz_to_en = load_glossary()
print(f"OK  glossary loaded: {len(en_to_dz)} entries")
if en_to_dz:
    sample = next(iter(en_to_dz))
    assert lookup(sample.upper() + "!", "eng_Latn") == en_to_dz[sample]
    print(f"OK  lookup works for: {sample!r}")
else:
    print("NOTE glossary is empty, so no overrides yet. Add verified entries to data/glossary.csv")

print("\nAll quality checks passed.")