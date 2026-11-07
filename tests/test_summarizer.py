import io

from core.documents import DocumentError, clean_text, extract_text
from core.summarizer import chunk_text, detect_language, tidy_summary, unsupported_numbers
from core.translator import DZ, _chop_dzongkha, _chop_english, _join_pieces

# 1. Re-joining lines that were only wrapped by the page
assert clean_text("This is a long\nline that wraps.\n\nNew paragraph.") == \
    "This is a long line that wraps.\nNew paragraph."
assert clean_text("inter-\nnational trade grows.") == "international trade grows."
print("OK  clean_text")

# 2. Long English sentences are cut at commas, no words lost
long_sentence = ", ".join(" ".join(["word"] * 10) for _ in range(10)) + "."
pieces = _chop_english(long_sentence)
assert len(pieces) > 1 and all(len(p.split()) <= 45 for p in pieces)
assert sum(len(p.split()) for p in pieces) == 100
print("OK  long English sentences are cut safely")

# 3. Long Dzongkha sentences are cut, no characters lost
tib = "ཀ་" * 300
pieces = _chop_dzongkha(tib)
assert len(pieces) > 1 and all(len(p) <= 220 for p in pieces)
assert "".join(pieces) == tib
print("OK  long Dzongkha sentences are cut safely")

# 4. Pieces are joined with one sentence end only
assert _join_pieces(["ཀ།", "ཁ།"], DZ) == "ཀ ཁ།"
print("OK  join pieces")

# 5. Splitting a text into parts
text = " ".join("This sentence has six words." for _ in range(10))
chunks = chunk_text(text, 20)
assert all(len(c.split()) <= 20 for c in chunks)
assert sum(len(c.split()) for c in chunks) == 50
print("OK  chunk_text")

# 6. Number check
assert unsupported_numbers("The fee is Nu 5 per day for 14 days.", "The fee is Nu 5 for 15 days.") == ["15"]
assert unsupported_numbers("It costs 1,000 now.", "It costs 1000.") == []
print("OK  number check")

# 7. Language guess
assert detect_language("Hello world") == "en"
assert detect_language("ཀ་ཁ་ག་") == "dz"
assert detect_language("Hello ཀ་ཁ་ག་ཀ་ཁ་ག་ world") == "mixed"
print("OK  detect_language")

# 8. Tidy the AI output
assert tidy_summary("**Key** point.\n- Second point.\n1. Third point.") == \
    "Key point.\nSecond point.\nThird point."
print("OK  tidy_summary")

# 9. Reading files
assert extract_text("a.txt", "Hello\nworld.".encode("utf-8")) == "Hello world."
assert extract_text("b.txt", "ཀ་ཁ།".encode("utf-8")) == "ཀ་ཁ།"

from docx import Document
d = Document()
d.add_paragraph("First paragraph.")
d.add_paragraph("Second paragraph.")
buf = io.BytesIO()
d.save(buf)
text = extract_text("c.docx", buf.getvalue())
assert "First paragraph." in text and "Second paragraph." in text
print("OK  TXT and DOCX reading")

# 10. Bad files give a friendly error
for name, data in [("x.exe", b"x"), ("x.txt", b""), ("x.docx", b"not a docx"), ("x.pdf", b"not a pdf")]:
    try:
        extract_text(name, data)
    except DocumentError as e:
        print(f"OK  {name}: {e}")
    else:
        raise AssertionError(f"{name} should have been rejected")

print("\nAll summarizer checks passed.")
