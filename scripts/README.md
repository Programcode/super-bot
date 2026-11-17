# scripts

- `ask-pip.sh`: send a question, decision request, status, result, or blocker to Pip. See "Talking to Pip" in `CLAUDE.md`. Needs `.env.pip` (gitignored; template in `.env.pip.example`).
- Page sync: there is no script here. Pip regenerates `docs/super-bot-page.md` from the Grok Bot page whenever it changes. See [`docs/sync.md`](../docs/sync.md).
