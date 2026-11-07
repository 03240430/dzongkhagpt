import time

from core import config
from core.translator import DZ, EN, translate

SENTENCES = [
    "Hello. How are you today?",
    "Thimphu is the capital of Bhutan.",
    "The weather is cold today.",
    "The school library opens at 8 am from Monday to Friday.",
    "Students can borrow up to 3 books at a time for 14 days.",
    "A book that is returned late costs Nu 5 for each day.",
    "Please give your name to the librarian before 30 November.",
    "Many tourists visit Bhutan every year.",
]

print(f"Translator: {config.NLLB_CT2_DIR}   beam size: {config.CT2_BEAM}")
translate("warm up.", EN, DZ)          # load the model first so the timing is fair

total = 0.0
for s in SENTENCES:
    start = time.time()
    dz = translate(s, EN, DZ)
    took = time.time() - start
    total += took
    back = translate(dz, DZ, EN)
    print(f"\nEN  : {s}\nDZ  : {dz}\nBACK: {back}\n({took:.1f}s)")

print(f"\nTotal time: {total:.1f}s for {len(SENTENCES)} sentences")