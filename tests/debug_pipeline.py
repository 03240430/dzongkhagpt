from core import llm
from core.chat_engine import SYSTEM_PROMPT
from core.translator import translate, EN, DZ

print("1. one sentence:")
print(translate("Thimphu is the capital of Bhutan.", EN, DZ))

print("\n2. two sentences in one batch:")
print(translate("Thimphu is the capital of Bhutan. The weather is cold today.", EN, DZ))

print("\n3. what the AI writes with the new prompt:")
english = llm.generate(
    SYSTEM_PROMPT,
    [{"role": "user", "content": "What is the capital of Bhutan?"}],
)
print(english)

print("\n4. that answer translated:")
print(translate(english, EN, DZ))