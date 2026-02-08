This pipeline expects `data/references.yaml` with:
- `topic`: string
- `contribution_statement`: string (multiline ok)
- `papers`: list of items, each with:
  - `id`: unique like P1, P2...
  - `citation`: short cite string for in-text use
  - `pid`: persistent identifier (doi:, arxiv:, acl:, url:)
  - `summary`: human-authored factual summary based on reading
  - `strengths`: list of strings
  - `limitations`: list of strings
  - `relation_to_work`: human-authored comparison to your contribution
  - `comments`: extra notes
The LLM is instructed to:
- cluster papers into taxonomy (no invention)
- draft related work using ONLY these inputs
- flag unsupported claims as [NEEDS HUMAN CHECK]
