import ctranslate2
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from core import config

sents = ["Thimphu is the capital of Bhutan.", "The weather is cold today."]

tok = AutoTokenizer.from_pretrained(config.NLLB_MODEL)
tok.src_lang = "eng_Latn"
print("Source tokens:", tok.convert_ids_to_tokens(tok.encode(sents[0])))

# A: the old PyTorch way
model = AutoModelForSeq2SeqLM.from_pretrained(config.NLLB_MODEL).eval()
for s in sents:
    inp = tok(s, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(
            **inp,
            forced_bos_token_id=tok.convert_tokens_to_ids("dzo_Tibt"),
            num_beams=1, max_new_tokens=60,
        )
    print("PyTorch            :", tok.batch_decode(out, skip_special_tokens=True)[0])

# B: the fast way, with two ways of building the input tokens
tr = ctranslate2.Translator(str(config.NLLB_CT2_DIR), device="cpu", compute_type="int8")


def ct2(s, manual):
    if manual:
        toks = ["eng_Latn"] + tok.convert_ids_to_tokens(
            tok.encode(s, add_special_tokens=False)) + ["</s>"]
    else:
        toks = tok.convert_ids_to_tokens(tok.encode(s))
    r = tr.translate_batch([toks], target_prefix=[["dzo_Tibt"]], beam_size=2)
    ids = tok.convert_tokens_to_ids(r[0].hypotheses[0][1:])
    return tok.decode(ids, skip_special_tokens=True)


for s in sents:
    print("CT2 (tokenizer)    :", ct2(s, False))
    print("CT2 (manual tokens):", ct2(s, True))