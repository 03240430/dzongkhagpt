import time
from core import llm
from core.translator import translate, EN, DZ


def step(name, fn):
    print(f"\n--- {name} ---")
    start = time.time()
    try:
        print(fn())
        print(f"OK ({time.time() - start:.1f}s)")
    except Exception as e:
        print("FAILED:", e)


step("1. AI model",
     lambda: llm.generate("You are a helpful assistant.",
                          [{"role": "user", "content": "Say hello in one short sentence."}]))

dz_holder = {}

def en_to_dz():
    dz_holder["text"] = translate("Hello. How are you today?", EN, DZ)
    return dz_holder["text"]

step("2. English -> Dzongkha (first run downloads ~2.4 GB)", en_to_dz)
step("3. Dzongkha -> English (round trip)",
     lambda: translate(dz_holder.get("text", ""), DZ, EN))