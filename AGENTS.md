# AGENTS.md

## Project Goal

This project builds a local daily literature digest workflow for me, a PhD student in computational materials and AI-for-materials.

The system shall:
1. Read recent academic alert emails from a dedicated Gmail account that subscribes to Google Scholar alerts and other journals/sources.
2. Extract paper entries from Google Scholar alerts and journal alert emails.
3. Deduplicate papers by DOI, URL, normalized title, and fuzzy title similarity.
4. Rank relevance to the user's research interests.
5. Translate and summarize paper titles, abstracts, and content into Chinese.
6. Generate a daily Markdown digest.
7. Optionally send the digest by email.

## Research Interests

Prioritize papers related to:
- computational materials science
- AI for materials
- pentagonal materials (especially those with pentagon-based structural motifs, e.g., penta-graphene): atomic systems, framework materials (COF, MOF)
- machine-learning interatomic potentials
- thermal transport, phonons, thermal conductivity

## Engineering Constraints

- Use Python.
- Prefer a small, reproducible project structure.
- Store secrets outside git.
- Never print API keys, OAuth tokens, refresh tokens, or email credentials.
- Keep `config.local.yaml`, `credentials.json`, `token.json`, `.env`, and `data/` out of git.
- First implement a dry-run mode before sending real emails.
- Add tests for parsing and deduplication.
- Do not delete emails.
- Provide an option to mark emails as read (configurable).
- The project shall also include a maintainable document for recent research interests, allowing the daily digest's recommendation priority to be updated based on textual descriptions of current research interests.

## Expected Daily Output

The daily digest should include:
1. Overall statistics:
   - emails read
   - paper entries extracted
   - duplicates removed
   - high-relevance papers
   - medium-relevance papers
   - Summary of Recent Research Interests
2. High-relevance papers, with Chinese summary and paper links. (Can be stratified by research keywords.)
3. Medium-relevance papers, with short Chinese notes and paper links. (Can be stratified by research keywords.)
4. Low-relevance papers, optionally listed only by title and link. (Can be stratified by research keywords.)

## Verification

Before considering a change complete:
- Run unit tests.
- Run the workflow in dry-run mode.
- Confirm a Markdown digest is created in `outputs/`.