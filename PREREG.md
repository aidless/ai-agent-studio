# Protocol note (not a preregistration)

Nothing in this file was filed before the code existed. There is no
external timestamp, no frozen analysis plan, and no hold-out that was
locked before looking at the encoder. Do not cite this document as a
preregistration.

## What the hash gate actually checks

`eval/negative_retrieval.py` builds a two-note index with
`_hash_embedding`:

- `sem.md`: `研究员在回答之前检索知识库。`
- `lex.md`: `banana banana lexical marker`

The English sentence `An analyst looks up notes first and then replies.`
is the negative query. The encoder's only features are character
trigrams (`app/rag/vector_store.py`). The gate fails unless all of these
hold on a fresh run:

1. That English sentence shares zero trigrams with `sem.md`.
2. Its cosine with `sem.md` is under 0.5. An exact copy scores 1. The
   ceiling is deliberately loose; the measured value is an output in
   `results/negative-hash.json`, not a number that was fit to pass.
3. Querying the exact `sem.md` text returns `sem.md` at distance 0.
4. Querying the exact `lex.md` text returns `lex.md`.
5. `semantic_retrieval_supported` is false.

A Chinese rephrase, `分析员会先查资料再作答。`, is stored in the same
JSON and is not part of the pass/fail rule. It also shares zero trigrams
with the relevant note. Its distance margin against the unrelated note is
under 0.01, small enough that a library change could flip the rank. The
English pair is the gated one: no shared features, and a wider gap.

## What would be required before a retrieval-quality claim

A semantic encoder, a query set frozen by hash before the run, a metric
named before the run, and a negative control that is not "the encoder's
own definition." None of that is in this repository. `results/negative-onnx.json`
is one extra pair on Chroma's default embedder, recomputed only with
`--onnx`, and it is not a substitute.

## LLM

There is no protocol for model answers. `test_agent` skips when
`DEEPSEEK_API_KEY` is unset. Skipping is not a result.
