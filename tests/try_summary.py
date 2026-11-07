from core.summarizer import summarize
from core.translator import translate, EN, DZ

ENGLISH = (
    "The school library will open at 8 am from Monday to Friday. "
    "Students can borrow up to 3 books at a time for 14 days. "
    "A book that is returned late costs Nu 5 for each day. "
    "Students who lose a book must pay its full price. "
    "The library will also start a reading club on Wednesdays after class. "
    "Anyone who wants to join the club should give their name to the librarian before 30 November."
)

last = {"msg": ""}


def show(frac, msg):
    if msg != last["msg"]:
        print(f"  {frac:4.0%}  {msg}")
        last["msg"] = msg


print("=== 1. English text -> Dzongkha summary ===")
r = summarize(ENGLISH, "short", "dz", on_progress=show)
print("Dzongkha summary:", r["summary"])
print("English draft   :", r["summary_en"])
print("Warnings        :", r["warnings"])
print(f"Time: {r['seconds']:.0f}s")

print("\n=== 2. Dzongkha text (made by translating the English above) -> Dzongkha summary ===")
dz_text = translate(ENGLISH, EN, DZ)
print("Input:", dz_text)
r2 = summarize(dz_text, "short", "dz", on_progress=show)
print("Dzongkha summary:", r2["summary"])
print("English draft   :", r2["summary_en"])
print("Warnings        :", r2["warnings"])
print(f"Time: {r2['seconds']:.0f}s")
