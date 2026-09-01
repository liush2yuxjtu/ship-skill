# Evals

`evals.json` contains four dry-run behavior cases:

1. Eve project without an eval suite;
2. existing suite missing coverage for a side-effecting HITL tool;
3. non-Eve repository with only an Eve guidance skill;
4. docs-only change with sufficient existing coverage.

Pi runner benchmark after iteration 3: new skill 100%, previous skill 55% across one run per configuration. These evals check planning behavior without mutating repositories or remotes.
