---
name: daily-report
description: Interview-driven daily report generator for concise engineering and project updates. Use when the user wants to turn spoken daily work updates, current version issues, test results, expert feedback, attachments, or coordination needs into a standalone Chinese HTML daily report.
---

# Daily Report

Use this skill to collect the user's current-day work first, enrich it with supplied evidence, confirm the proposed summary, and then generate or iteratively revise a standalone HTML daily report. Treat the weekly report as the macro direction and the daily report as the detailed execution log; revise the daily report only unless the user explicitly asks to revise the weekly report.

## What to reuse from weekly-report

Reuse the visual language of `weekly-report`:

- restrained editorial palette, strong title hierarchy, single-column item cards, and printable A4 layout;
- visible status badges such as `已完成`, `已修复待测试`, `修改中`, `待批量测试`, `待确认`;
- mandatory attachment rows with local/cloud links and one-line evidence descriptions;
- local files copied into the same `YYMMDD日报` archive folder and linked with same-folder relative paths.

Do not copy the weekly interview sequence or its long historical review into a daily report. A daily report should be short, current, and action-oriented.

## Storage and source priority

- Use `D:\lijingSun\Doc\周报日报` as the archive root.
- Use the fixed archive layout: `D:\lijingSun\Doc\周报日报\YYMMDD日报\YYMMDD日报.html` and `D:\lijingSun\Doc\周报日报\YYMMDD日报\YYMMDD日报.md`. Create the current date folder when authorized to generate the report; do not use `YYMMDD周报` for daily reports.
- Resolve the previous-day source deterministically as `D:\lijingSun\Doc\周报日报\{previous-day YYMMDD}日报\{previous-day YYMMDD}日报.html`. Read that HTML for content continuity only; never use it as the visual or DOM template for today's report.
- Prioritize sources in this order: (1) the user's current-day oral update, (2) the previous day's daily report, (3) the current week's weekly report and its next-week plan, (4) today's supplied files, screenshots, logs, and test outputs. Use older weekly material only when continuity cannot be established from the current weekly report.
- Do not let an older report override the user's current-day status. If sources conflict, use the user's latest statement and flag only material discrepancies.

## Interview workflow

Start with one focused question:

> 请先描述一下你今天做了什么、哪些问题有变化、哪些结果最值得汇报？

After the oral update:

1. Split the update into candidate items without rewriting away the user's facts.
2. Offer 2–3 possible ways to organize the day's content, for example: `开发推进优先`, `问题修复优先`, or `测试验证优先`; recommend one based on the user's facts and let the user accept, modify, or choose another.
3. Ask focused follow-ups for missing owner, status, verification result, next action, coordination need, or attachment. Provide short candidate answers instead of asking the user to write a large form.
4. Read the previous day's daily report, the current weekly report and its plan, and only the supplied current-day materials needed for continuity. Do not load unrelated historical material.
5. Explain how the daily details connect to the weekly direction, identify stale or over-detailed content, and give 2–3 candidate executive summaries.
6. Ask the user to confirm the proposed four sections before generating HTML.
7. Generate only after the user confirms. Later browser comments or user edits should update the current HTML in place and preserve confirmed facts.

## Required report structure

Use these four sections unless the user explicitly changes the structure:

1. **当前开发工作进展**
   - State what was completed today and what integration or development is underway.
   - Prefer short numbered points when there are multiple activities.

2. **当前版本问题修复与进展**
   - Give every problem its own row/card.
   - Use the fixed fields `问题`, `处理方法`, `当前状态`, and `下一步/验证`.
   - Preserve the user's status wording. Do not turn “待测试” into “已完成”.

3. **测试问题及遗留问题**
   - Separate actual test results from unresolved issues.
   - Show batch runs, self-tests, expert evaluation, failed cases, and pending verification as separate points.
   - Include sample counts, affected items, or validation status only when supplied by the user.

4. **需要协调的问题**
   - List each coordination request as a separate numbered point.
   - State the required resource, decision, owner, or dependency when known.

5. **明日计划**
   - Add this as a visible closing module in both HTML and Markdown whenever the user provides a next action or explicitly asks for the module.
   - Keep the same single-column card style and status/attachment conventions as the other sections.
   - Do not invent tomorrow's plan; preserve the user's wording and distinguish planned verification from completed work.

## Daily-versus-weekly boundary

- Keep the weekly report at the level of direction, milestones, major results, and leadership attention.
- Keep the daily report at the level of today's actions, individual bugs, test cases, verification status, prompt or code changes, and concrete coordination needs.
- Do not duplicate an entire weekly paragraph into the daily report. Use the previous day's report and weekly plan to establish continuity, then write only today's delta and evidence.
- If a daily issue changes the weekly conclusion materially, flag it to the user; do not silently modify the weekly report.

## User-facing options

At key planning points, give the user options they can select directly:

- **内容重点**: `开发推进优先` / `问题修复优先` / `测试验证优先`.
- **日报密度**: `领导精简版` / `标准日报版（推荐）` / `技术留痕版`.
- **连续性范围**: `上一天日报 + 本周周报（推荐）` / `只读上一天日报` / `只按今日口述`.

Default to `标准日报版` and `上一天日报 + 本周周报`; explain the trade-off in one sentence and let the user change it.

## Status normalization

Keep the user's meaning while using consistent visible badges:

- `已完成` / `已修复`
- `已修复待测试验证`
- `修改中` / `优化中`
- `待批量测试验证`
- `待确认` / `待补充`
- `阻塞 / 需要协调`

When the user provides a sentence such as “已修复待测试验证”, keep both parts visible; completion and verification are different states.

## Mandatory attachments

Every development item, version issue, test result, and coordination item must have an attachment block, even if the block says evidence is not yet available.

Ask separately:

> 本地附件是否存在？云端附件是否存在？这个附件能证明什么？

For each attachment:

- include a human-readable name;
- preserve the original supplied path in readable text;
- use a clickable same-folder relative link for copied local files;
- keep a clickable cloud URL when supplied;
- add one sentence explaining what the attachment proves;
- if missing, show `附件（必填）` and `待补充本地附件`; never invent a link.

## Confirmation gate

Before generation, present a compact checklist:

- 当前开发工作进展是否准确？
- 版本问题及修复状态是否准确？
- 批跑、自测、专家评判结果及遗留问题是否准确？
- 需要协调的问题是否准确？
- 附件是否已经补齐，哪些仍需补充？

Ask: `以上四部分是否确认？确认后我再生成 HTML 日报。` Do not generate before an affirmative answer.

## HTML delivery

- Use `assets/daily-report-template.html` as the only visual, CSS, DOM, and component reference. The rendered HTML must visibly contain these exact section titles: `当前开发工作进展`, `当前版本问题修复与进展`, `测试问题及遗留问题`, and `需要协调的问题`.
- Do not copy layout, CSS, DOM structure, or visual styles from the previous day's HTML. The previous day's HTML is a content source only.
- Any added `明日计划` module must reuse the template's existing section/card and attachment components so all daily reports remain visually consistent.
- Produce one self-contained `.html` file with inline CSS and JavaScript only.
- Keep the report printable on A4, readable on desktop/mobile, and visually consistent with the weekly report.
- Put the top-level conclusion and status summary before the four detail sections.
- Use one-column cards; avoid dashboard-style tall metric columns and avoid long undivided paragraphs.
- Use semantic headings, accessible status text, visible focus styles, sufficient contrast, and print styles.
- Before delivery, verify that every item has an attachment block, every local relative link resolves inside the current report folder, all user placeholders are replaced, and no data was invented.

## Markdown and terminal delivery

- In addition to the HTML report, generate a Markdown daily report in the same `YYMMDD日报` archive folder, using a matching filename such as `YYMMDD日报.md`.
- The Markdown report is the copy-ready group-message version. It must summarize the confirmed HTML content rather than mechanically copying every sentence from the HTML.
- Use five numbered top-level sections in this order:
  1. `当前开发工作进展`
  2. `当前版本问题及修复进展`
  3. `批跑、自测、专家评判结果及遗留问题`
  4. `需要协调的问题`
  5. `明日计划`
- Under each section, use indented `○` sub-items. Keep every confirmed issue, status, test result, unresolved problem, and coordination item; do not omit concrete points while summarizing.
- The `明日计划` section must be included when the user supplies or requests a next-day action; include only confirmed planned actions, such as pending verification.
- When the user provides a Codex thread ID or deep link, read the thread and inspect its file mentions, screenshots, file-change records, generated artifacts, and referenced local/cloud attachments. The thread URL/ID is not itself an attachment.
- For every accessible thread attachment, verify the source path or URL, copy accessible local files into the fixed current-day archive folder, preserve the original path or cloud reference, and register the imported file in both HTML and Markdown with a one-line evidence description. If an attachment cannot be accessed or exported, explicitly mark it as unavailable; never claim it was imported.
- Keep the report body at executive-summary granularity: summarize major work items, outcomes, status, and next actions. Do not put individual keywords, scoring-point text, or detailed test-case/problem examples in the main sections unless the user explicitly asks for detail; place such evidence in the attachment area instead.
- Preserve user-confirmed status meanings and bold important statuses, for example `**已完成修复**`, `**已修复待测试验证**`, `**修改中**`, `**正在开发评分逻辑**`, and `**待批量测试验证**`.
- When presenting the Markdown content in the terminal or chat, wrap the copy-ready report in a fenced `text` code block so it can be copied directly to a group chat. Do not add commentary inside the code block.
- Do not change the HTML merely to produce the Markdown version. The Markdown is a separate delivery artifact derived from the confirmed report content.
