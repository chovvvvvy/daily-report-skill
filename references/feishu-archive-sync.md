# Feishu archive sync

Run this post-generation workflow only after the user has confirmed the complete report and the canonical JSON, HTML, and Markdown have passed local delivery checks. The user's standing instruction authorizes these exact archive writes without a new confirmation on every run.

## Configuration

Read `C:\Users\eqy\.codex\report-sync\feishu-archive.json` before writing.

- Require `enabled: true`, `status: configured`, and non-empty `report_folder_token` and `attachment_folder_token`.
- Under `report_folder_token`, create or reuse a per-report date subfolder named `YYYYMMDD` (for example `20260817`), and place only that report's native Markdown and corresponding HTML file inside it.
- Under `attachment_folder_token`, create or reuse a matching per-report date subfolder named `YYYYMMDD`, and place only that report's confirmed attachments referenced by the canonical JSON inside it.
- Do not import Markdown as Docx and do not create an additional online document.
- Never fall back to Drive root or another folder when a token is missing or invalid.

## Naming

Build a short factual `core_topic` from the confirmed report conclusion. Use `工作进展` only when there is no single dominant topic. Do not rename local canonical files; apply these names only to Feishu archive objects.

- Daily Markdown and HTML: `YYYYMMDD_日报 - {core_topic}.md|html`
- Weekly Markdown and HTML: `YYYYMMDD_周报 - {core_topic}.md|html`
- Attachment: `YYYYMMDD_{日报|周报} - {core_topic} - 附件 - {original_name}`

## Sync order

1. Create or reuse the report date subfolder under `report_folder_token` using the `YYYYMMDD` name (for example `20260817`), and record its folder token in the manifest.
2. Create or reuse the attachment date subfolder under `attachment_folder_token` using the same `YYYYMMDD` name, and record its folder token in the manifest.
3. Create the native Markdown in the report date subfolder with `lark-cli markdown +create --as user`; when the manifest already records its `file_token`, use `markdown +overwrite` instead.
4. Upload the HTML to the report date subfolder with `lark-cli drive +upload --as user`; when the manifest records its `file_token`, pass that token to overwrite it.
5. Upload each confirmed attachment to the attachment date subfolder; never sweep unrelated files from the local report directory.
6. Write `YYMMDD日报.feishu.json` or `YYMMDD周报.feishu.json` beside the local report. Record both root tokens, both date-subfolder tokens, all returned file tokens/URLs, local SHA-256 values, and `synced_at`; store no secrets.

All `lark-cli --file` paths must be relative to the command CWD. Treat only `ok: true` or exit code `0` as success. Execute writes serially.

## Idempotency and completion checks

- If the manifest exists and every SHA-256 still matches, skip duplicate writes and return the recorded links.
- If a local file changed, overwrite the object recorded in the manifest rather than creating a duplicate.
- If a recorded token no longer resolves, stop that sync and report the exact missing object; do not create an untracked replacement.
- Confirm that both `.md` and `.html` are in the report date subfolder, all confirmed attachments are in the attachment date subfolder, names follow the applicable daily/weekly convention, and every manifest token came from a successful CLI response.
