---
name: daily-report
description: Continuity-first Chinese daily report workflow for developers. Use when the user wants to review yesterday's promised work, record today's engineering progress, bugs, tests, temporary additions, evidence, and tomorrow's plan, then generate consistent JSON, HTML, and Markdown daily reports.
---

# Daily Report

Generate a short developer daily report that first checks yesterday's commitments, then records today's additions. Keep the daily report aligned with the current weekly plan and never let an unfinished item disappear without explanation.

## Core contract

- Read the previous valid daily report before asking what the user did today.
- Start by showing what yesterday said should be done today; verify those items one by one before collecting new work.
- Keep the same `item_id` for the same work item across daily and weekly reports.
- Treat the reporter as the default owner. Do not repeat the owner's name on every item unless the report combines multiple people.
- Generate the report each evening. Record `report_date`, `data_cutoff`, and `generated_at` separately.
- Treat every confirmed item under today's `明日计划` as an explicit next-day commitment. Preserve its `item_id` and carry it into the next day's `昨日承诺兑现` section for one-by-one reconciliation before collecting new work.
- Use one confirmed structured fact source for every output. Never edit HTML and Markdown as independent versions.
- Preserve the user's latest statement as authoritative. Flag material conflicts with older reports instead of guessing.

## Storage and canonical source

Use `D:\lijingSun\Doc\周报日报` as the archive root and create:

- `YYMMDD日报\YYMMDD日报.json` — canonical confirmed facts;
- `YYMMDD日报\YYMMDD日报.html` — leadership-readable report generated from the JSON;
- `YYMMDD日报\YYMMDD日报.md` — copy-ready group message generated from the same JSON.

Update the JSON first during every revision, then regenerate both derived files. Before delivery, verify that item IDs, statuses, results, and next actions match across all three files.

Use this minimum item schema:

```json
{
  "item_id": "W-YYYYWW-01",
  "source_type": "weekly_commitment | carried_daily | temporary_addition",
  "title": "事项名称",
  "yesterday_commitment": "昨天承诺今天完成的内容",
  "today_delta": "今天实际发生的变化",
  "execution_status": "待确认 | 未开始 | 进行中 | 已完成 | 阻塞 | 取消",
  "validation_status": "待确认 | 无需验证 | 待验证 | 已通过 | 未通过",
  "schedule_status": "待确认 | 正常 | 有风险 | 已延期",
  "result": "结果或验收结论",
  "next_action": "下一步",
  "due_date": "日期或待确认",
  "addition_reason": "仅临时新增事项填写",
  "attachments": []
}
```

Prefer the weekly item ID. If an item is first created in a daily report, assign `D-YYMMDD-01`; preserve it on later days and map it to a weekly item when the weekly report includes it.

## Source resolution

1. Read yesterday's daily JSON. If it does not exist, read yesterday's HTML and Markdown and compare their `明日计划` content.
2. If yesterday has no report, use the latest previous valid daily report and state its actual date.
3. Read the current weekly report's open commitments and IDs.
4. Read only today's supplied files, screenshots, logs, test outputs, or threads needed to verify current changes.
5. If HTML and Markdown disagree, stop and show the conflict; ask which statement is correct before carrying it forward.

Previous reports establish commitments, not today's truth. The user's current confirmation always determines today's final status.

## Interview workflow

### 1. Present today's commitment baseline

Extract yesterday's `明日计划` and unresolved carried items. Before asking for new work, show a compact list:

| 事项编号 | 昨日承诺 | 今日应形成的结果 | 当前状态 |
|---|---|---|---|
| W-YYYYWW-01 | 原计划 | 可验收结果 | 待用户确认 |

Ask one focused question at a time: `这项工作今天是否已完成？请选择：已完成 / 进行中 / 未开展 / 阻塞 / 取消，并补充实际结果。`

For each item, confirm:

- today's actual change or result;
- execution, validation, and schedule status;
- next action and due date when unfinished;
- reason when delayed, cancelled, or changed.

Do not move to additions until every baseline item is reconciled. An item may be completed, continued, delayed, cancelled, or explicitly transferred; it may not silently disappear.

### 2. Collect today's additions

Only after the baseline is complete, ask: `除上述承诺事项外，今天是否还有临时新增工作？`

Classify every addition as:

- linked to an existing weekly commitment; or
- `temporary_addition`, with a short reason such as urgent defect, new requirement, or production support.

Do not force unrelated work into an existing weekly item.

### 3. Reconcile with the weekly direction

Show how each daily item maps to the weekly plan. Flag:

- a weekly commitment that is now at risk or overdue;
- a temporary addition that materially changes weekly priorities;
- conflicting completion or validation claims;
- an open item with no next action.

### 4. Confirm and generate

Present the proposed continuity summary, detailed sections, statuses, and tomorrow's commitments. Generate files only after the user confirms the facts.

## Status rules

Use three independent dimensions:

- execution: `待确认 / 未开始 / 进行中 / 已完成 / 阻塞 / 取消`;
- validation: `待确认 / 无需验证 / 待验证 / 已通过 / 未通过`;
- schedule: `待确认 / 正常 / 有风险 / 已延期`.

Do not collapse `已完成 + 待验证` into fully verified completion. Do not turn `待测试` into `已完成`. If the user uses another phrase, preserve its meaning and map it visibly to these dimensions.

## Report structure

Place a required `昨日承诺兑现` overview before the details. Then use these five sections:

1. **当前开发工作进展** — today's actual delta and visible results;
2. **当前版本问题修复与进展** — `问题 / 处理方法 / 当前状态 / 下一步或验证`;
3. **测试问题及遗留问题** — separate completed tests, failed cases, and pending validation;
4. **需要协调的问题** — preserve confirmed coordination content; write `无` when none;
5. **明日计划** — carry only confirmed next actions, each with the same item ID and expected result.

Keep one primary record per item. Do not rewrite the same Java integration, defect, or test item independently in several sections; refer to the primary item when another section needs it.

## Attachments

Treat attachments as optional supporting evidence, not mandatory fields.

- Ask for an attachment when it better demonstrates a deliverable, test result, metric, screenshot, report, or decision.
- Do not create `待补充附件` placeholders when no attachment is needed.
- When supplied, include a readable name, original path or URL, clickable same-folder relative link, and one sentence explaining what it demonstrates.
- Copy accessible local attachments into the current `YYMMDD日报` folder.
- Never invent a link or claim to have inspected an unavailable file.

## Output rules

- Use `assets/daily-report-template.html` as the visual and component reference; preserve its restrained editorial style, single-column cards, accessibility, responsive layout, and A4 print styles.
- Generate HTML and Markdown only from the confirmed JSON model.
- Keep the HTML's top sequence: date and cutoff → yesterday commitment fulfillment → today's conclusion → details → tomorrow plan.
- Use the same five numbered sections in Markdown and retain every confirmed item ID, status, result, and next action.
- Put copy-ready Markdown in a fenced `text` block when showing it in chat.
- When revising a report, update JSON first and regenerate both outputs; never patch only one derivative.

## Delivery checks

Before delivery, verify:

- every yesterday commitment has an explicit outcome;
- every unfinished item has a next action and due date or `待确认`;
- every temporary addition has a reason;
- the same item keeps the same ID across daily and weekly sources;
- execution, validation, and schedule statuses do not contradict each other;
- HTML and Markdown match the canonical JSON;
- all supplied local links resolve inside the report folder;
- no facts, metrics, dates, or evidence were invented.
