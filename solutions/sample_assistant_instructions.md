# Sample User Instructions for Genie Code

These are the instructions to paste into your `.assistant_instructions.md`
file during **Part 5** of the lab.  After saving the file, re-run the same
prompt you used in the baseline step and observe how Genie Code's output
changes — naming, structure, comment style, library choices, and SQL form
all shift to match the rules below.

The full file content (everything inside the fenced block) is what you copy
into your `.assistant_instructions.md`.

---

```markdown
# My Genie Code instructions

## Coding conventions
- Always use PySpark for data work; alias `pyspark.sql.functions` as `F`.
- Add type hints to every function signature.
- Write docstrings in Google style with `Args` and `Returns` sections.
- Prefer `.transform()` chains over reassignment to a `df` variable when
  building multi-step transformations.

## SQL preferences
- When generating SQL, prefer common table expressions (CTEs) over nested
  subqueries — readability beats brevity.
- Default catalog is `workspace`, default schema is `genie_code_lab`. Don't
  fully qualify table names unless crossing schemas.
- Always include explicit column lists; never `SELECT *` in production code.

## Tone and structure
- Keep code comments terse — only explain *why*, never *what*.
- When proposing a fix, first state the root cause in one sentence, then
  show the diff. Don't summarize the fix afterward.
- For non-trivial pipelines, include a 3-line ASCII data-flow diagram in
  the leading docstring.
```
