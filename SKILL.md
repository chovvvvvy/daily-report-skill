---
name: daily-report
description: Continuity-first Chinese daily report workflow for developers, including confirmed Feishu archive synchronization and guarded headless submission of the four daily-report text fields.
---

# Daily Report

Generate a concise developer daily report by project: check yesterday's commitments, record today's actual project progress and other work, and keep follow-up actions with their related items. Keep the report aligned with the current weekly plan; unfinished items never disappear without explanation.

## Report model

Use GPT-6 Luna (`gpt-6-luna`), reasoning `low`, and Fast for report content preparation and generation. Follow [shared model execution rules](references/report-model.md) before drafting. Skills cannot switch the active chat model; use the dedicated `reporting-luna-fast` profile when a separate generation call is needed. The current chat retains user confirmation, deterministic validation, archive and workbench/Feishu synchronization. Do not silently substitute another model.

## Core contract

- Read the previous valid daily report before asking what the user did today.
- Present one complete project-grouped checklist of yesterday's commitments, today's known evidence, workbench edits, other work, and known questions. Accept one oral or numbered batch reply covering all projects and additions; do not interview one project or item at a time.
- Keep the same `item_id` for the same work item across daily and weekly reports. The board now tracks persistent items from `items[]`; dated actions in `tomorrow_plan[]` remain independent children. Read unresolved `candidate.tasks`, item state events and notes alongside previous commitments; omission in a later report never closes an item. For an explicitly confirmed cross-week ID mapping, use the same optional `work_item_id` on the item and its actions, never infer it from a title or `parent_item_id`.
- Treat the reporter as the default owner. Do not repeat the owner's name on every item unless the report combines multiple people.
- Generate the report each evening. Record `report_date`, `data_cutoff`, and `generated_at` separately.
- Preserve each confirmed follow-up action and its linked `item_id`; use `item_id: null` for a project-level or otherwise unlinked action, with `project_id: null` too when ownership is unknown. Such an action remains a plan and creates no work-item card. Only schedule it on a concrete day when the user supplied that day (including an explicit relative date such as 明天). The `tomorrow_plan` field name alone does not assign a date. Unscheduled actions remain available to the next batch review.
- Use one confirmed structured fact source for every output. Never edit HTML and Markdown as independent versions.
- Preserve the user's latest statement as authoritative. Flag material conflicts with older reports instead of guessing. When a confirmed report reconciles a manually changed persistent item, write its exact observed `workbench_task_revision` on that item. Re-read after a conflict; a missing acknowledgement preserves the manual state. The board state, action state and validation state are separate; completing an action does not close its parent item.
- Group actual work by its confirmed primary `project_id`; a related project is a reference, not a duplicate result. Known projects use their registered IDs. Do not infer a historical project's ownership from similar titles or split an existing `item_id` to fit the layout. Unattributed work stays in `其他工作与备注`.

## Storage and canonical source

Use `D:\lijingSun\Doc\周报日报` as the archive root and create:

- `YYMMDD日报\YYMMDD日报.json` — canonical confirmed facts;
- `YYMMDD日报\YYMMDD日报.html` — leadership-readable report generated from the JSON;
- `YYMMDD日报\YYMMDD日报.md` — copy-ready group message generated from the same JSON.

Update the JSON first during every revision, then regenerate both derived files. Before delivery, verify that item IDs, statuses, results, and next actions match across all three files.

Use the shared [project report schema](references/project-report-schema.md) for new reports: set `report_layout: "project-v1"` and `workbench_schema_version: 2`; provide `projects[]`, `items[]`, and `tomorrow_plan[]` even when empty, with optional `notes[]` and `decisions[]` only when present. Preserve existing item fields, including this minimum:

```json
{
  "item_id": "W-YYYYWW-01",
  "source_type": "weekly_commitment | carried_daily | temporary_addition",
  "parent_item_id": "所属周报事项 ID；无法映射时为 null",
  "project_id": null,
  "title": "事项名称",
  "yesterday_commitment": "昨天承诺今天完成的内容",
  "commitment_fulfilled": "是 | 否 | 不适用 | 待确认",
  "commitment_reason": "是否完成的事实原因；新增事项填写不适用原因",
  "today_delta": "今天实际发生的变化",
  "progress_status": "是 | 否 | 待确认",
  "progress_summary": "当前是否在进行及具体进程",
  "execution_status": "待确认 | 未开始 | 进行中 | 已完成 | 阻塞 | 取消",
  "validation_status": "待确认 | 无需验证 | 待验证 | 已通过 | 未通过",
  "schedule_status": "待确认 | 正常 | 有风险 | 已延期",
  "result": "结果或验收结论",
  "next_action": "下一步",
  "due_date": null,
  "addition_reason": "仅临时新增事项填写",
  "attachments": []
}
```

Every new `items[]` row explicitly includes `project_id` as a registered ID or null. Explicit null means unassigned and must not be inferred from a plan; only a legacy row missing this field may use a unique confirmed action project as a compatibility fallback. Optional `related_project_ids` only references other projects; `blocker`, `coordination`, and `resume_context` stay on the relevant item. Every new `tomorrow_plan[]` action explicitly includes `item_id` and `project_id`, each a confirmed value or null, plus `action` and `expected_result`; only `target_date`/`due_date` and existing ancillary fields are optional. An action may name another confirmed project independently of its linked item's primary project; it need not repeat that project in `related_project_ids` or change the item's ownership. A project-level action uses `item_id: null` and remains a plan, never a generated work-item card. A follow-up is not a result. `notes[]` holds pure notes without changing task state or counting as an accomplishment; actual tasks remain `items[]` even in `其他工作与备注`. `decisions[]` keeps `confirmed` and `proposed` distinct, with source references where available. If a note or decision cites an `item_id`, its supplied project must be that item's primary or explicitly related project. Use confirmed facts only for results, and retain unknown factual outcomes as `待确认`. Do not ask again solely to fill omitted optional fields.

Prefer the weekly item ID. If an item is first created in a daily report, assign `D-YYMMDD-01`; preserve it on later days and set `parent_item_id` when it belongs to a weekly commitment. A temporary addition may keep its `D-` ID until the next weekly review assigns a `W-` ID. Never silently replace or merge a daily item without recording the mapping.

## Source resolution

### Personal workbench facts

When the local star workbench exists, use [references/workbench-input.md](references/workbench-input.md) to read date-scoped candidate task changes, plan-linked notes, and relevant project iteration facts after resolving previous commitments. Include tasks changed today even when their planned execution date was earlier. Preserve item IDs, plan IDs, and source paths; count each note once. Pure board reordering is an audit event, and project ideas are future-work candidates rather than completed facts. These records supplement the single batch review; they do not bypass the confirmation gate or count execution completion as validation success. A project version marked candidate or a task marked complete does not prove release or acceptance.

1. Read yesterday's daily JSON. If it does not exist, read yesterday's HTML and Markdown and compare their follow-up actions and commitments, including any legacy `明日计划` section.
2. If yesterday has no report, use the latest previous valid daily report and state its actual date.
3. Read the current weekly report's open commitments and IDs.
4. Read only today's supplied files, screenshots, logs, test outputs, or threads needed to verify current changes.
5. If HTML and Markdown disagree, stop and show the conflict; ask which statement is correct before carrying it forward.

Previous reports establish commitments, not today's truth. The user's current confirmation always determines today's final status.

Before carrying items forward, validate supplied `parent_item_id` against the referenced weekly commitment. Several daily actions may share a weekly parent. Keep an absent mapping null; do not ask the user to create IDs or force temporary work into a weekly commitment. An old weekly plan is historical context, not a current-week schedule.

## Interview workflow

### 1. Present one complete project checklist

Read the previous valid daily JSON, current weekly plan, and workbench candidate once. Group every known yesterday commitment, unresolved item, dated plan action, today's workbench edit, and supplied evidence under its confirmed project. Put work with no confirmed primary project in `其他工作与备注`; do not guess a project from its title. Keep distinct actions under the same stable `item_id`, and show the actual source date when the previous report is older than yesterday. Already closed work is background unless it changed today. Present the entire scope at once, for example:

| 项目／事项 | 昨日承诺与已知状态 | 今日变化及来源 | 本次需核对 |
|---|---|---|---|
| 项目名 · 原事项 ID | 原承诺或无；昨日事实 | 今日证据支持的候选事实，或待确认 | 兑现与原因、当前进程、结果和下一步中尚不明确的实质事实 |

Include project-level plans, other actual work, pure notes, and known decisions in the same batch. Ask once for a natural-language or numbered reply covering all projects, additions, unfinished reasons, results/validation, blockers/coordination, and later actions. Offer optional execution and due dates together; if omitted, leave them null/absent. Cite source dates briefly and mark unconfirmed judgments as candidates. Without today's evidence, write `待确认`; yesterday's plan is never proof of today's progress. Do not search unrelated repositories or all task history merely to fill the checklist.

### 2. Reconcile the single reply

Before collecting the reply, cover **all active unfinished items**, not only items mentioned in yesterday's report. Read `candidate.task_review.open_ids` and `blocked_ids`, resolve each ID through `candidate.tasks`, and deduplicate with commitments and dated actions by stable identity. If this field is absent, derive the same sets from current tasks and explicit follow-up flags. Every eligible item must appear once in the batch or already have an explicit current-user answer; do not limit historical open items by report age or omit unscheduled work.

- For ongoing/unstarted items, show the last known state and actual source date, then ask about completion, continuation, blockage, cancellation, or temporary shelving, together with changed results/next actions. Prefill facts already confirmed in this conversation; do not ask them again.
- Keep blocked items visible with the known blocker, source date, and any known dependency/next trigger. List them under their project in the same batch and ask once whether any blocker changed. An explicit “all listed blockers unchanged” answer covers those listed items; silence does not. A recurring blocker is not a new daily achievement.
- `followup_state: shelved` pauses routine daily follow-up independently of execution status. Do not repeat progress questions or auto-resume a shelved item because a report mentions it. An explicit dated action or prior commitment still needs reconciliation; ask about its conflict with shelving once in the same batch. New user-supplied facts or an explicit resume instruction can make the item relevant again. Persist confirmed shelving/resumption through the shared CLI contract, never as completion, cancellation, or a blocker.

### 2. Reconcile the single reply

For each yesterday commitment, keep a separate `是否已完成` outcome and factual reason. For each actual work item, keep `是否进行` and current progress, today's change, result and validation, blocker/coordination when known, next action, and relevant location or reference. Attach defect, test, and coordination details to their related item. Project-only arrangements stay at the end of that project's group; a cross-project reference does not create another item or count the result twice. A pure note stays in `notes[]` and does not update a task or become a result. Keep confirmed decisions separate from proposals in `decisions[]`.

Classify supplied additions as existing-item work or `temporary_addition` with a short factual reason; do not force unrelated work into a weekly commitment. Show how each item relates to the weekly plan, including any risk, scope change, or conflicting completion/validation claim. List every known issue in the first batch. Do not ask separate project-by-project or field-by-field follow-ups. Leave missing factual conclusions as `待确认`; do not treat silence as completed, unchanged, or approved. Only material contradictions that alter a conclusion warrant one concentrated clarification; omitted optional dates, links, and other nonessential fields do not.

### 3. Final confirmation and generation

Check coverage for every active unfinished/blocked ID: answered, explicitly unchanged, newly shelved, or unanswered. Unanswered means today's progress is unknown; retain the last confirmed database execution state and source date. Do not overwrite it with `待确认` merely because today's reply omitted it. Mention unresolved coverage briefly in the final review without interviewing item by item. Unchanged blockers may remain as dated context, not newly achieved results.

Judge completion against the item's confirmed scope. Completed integration may have a separate outstanding deployment/validation action: do not keep the item indefinitely in progress because of that later action, or bulk-complete the action when closing the item. Clarify only material scope conflicts, retain stable IDs, and preserve user corrections with their source instead of silently rewriting old report facts.

Present one complete proposed review of the three report parts, every yesterday outcome and reason, project-item progress, other work/notes, decisions, and linked follow-up actions with any supplied dates. Generate files only after the user confirms this full review.

## Status rules

Use three independent dimensions:

- execution: `待确认 / 未开始 / 进行中 / 已完成 / 阻塞 / 取消`;
- validation: `待确认 / 无需验证 / 待验证 / 已通过 / 未通过`;
- schedule: `待确认 / 正常 / 有风险 / 已延期`.

Do not collapse `已完成 + 待验证` into fully verified completion. Do not turn `待测试` into `已完成`. If the user uses another phrase, preserve its meaning and map it visibly to these dimensions.

## Report structure

Render exactly these three main parts from the confirmed JSON:

1. **昨日承诺兑现** — group by confirmed project and retain every carried commitment separately, each with `是否已完成` (`是/否/不适用/待确认`) and a factual `原因`. A new item uses `不适用` with its addition reason; do not merge several promises into one sentence.
2. **项目推进** — group by primary project, then stable item. For each item show `是否进行` and `当前进程`, today's actual change, result and validation, any blocker/coordination, and its next action or dated arrangement. Put references and resume location on the same item. Render project-linked pure notes and decisions beside the corresponding item or project, clearly separate from results. Place a project-level arrangement with `tomorrow_plan[].item_id=null` at the end of that project's group. `projects[].summary` may give a concise confirmed overview but never replace item facts.
3. **其他工作与备注** — show real work without confirmed project ownership as `items[]` with the same progress and result fields. Show unlinked plans with `item_id: null, project_id: null` as plans only. Show unassigned pure `notes[]` as notes without claiming a task change or result, and unassigned decisions with `confirmed` or `proposed` status and known rationale/source; do not turn a proposal into a decision.

Defects, tests, and coordination belong to their related item, including cross-project work with one primary `project_id`. Keep one primary record per item and use `related_project_ids` only as references. Do not create independent problem-fix, test, coordination, or `明日计划` sections. Retain confirmed dated and undated follow-up actions in `tomorrow_plan[]` and render them next to their related item or at the project group end; an undated action is “后续安排”, not a claim that it is scheduled tomorrow.

## Attachments

Treat attachments as optional supporting evidence, not mandatory fields.

- Ask for an attachment when it better demonstrates a deliverable, test result, metric, screenshot, report, or decision.
- Do not create `待补充附件` placeholders when no attachment is needed.
- When supplied, include a readable name, original path or URL, clickable same-folder relative link, and one sentence explaining what it demonstrates. On desktop, place it in the related item's visually secondary 附件 rail; on narrow screens place the rail beneath the related narrative.
- When an item has no attachment, render the explicit text 无; do not invent a file, image, or pending-evidence placeholder.
- Copy accessible local attachments into the current `YYMMDD日报` folder. In Feishu, archive each report under matching `M.D` date subfolders below the configured report and attachment roots.
- Never invent a link or claim to have inspected an unavailable file.

## Output rules

- Use the shared fixed Python environment described in [references/report-runtime.md](references/report-runtime.md) for daily and weekly Python work. Run its local preflight once before delivery, not during each interview turn.

- Use `assets/daily-report-template.html` as the blue 当日追踪 visual shell and component reference, including accessible headings, responsive layout, and A4 print styles. Its sample copy is never an independent fact source.
- After confirmation, generate the same-stem HTML and Markdown deterministically from the canonical JSON with [render_project_report.py](scripts/render_project_report.py):

  ```powershell
  & 'C:\Users\eqy\.codex\report-sync\.venv\Scripts\python.exe' 'C:\Users\eqy\.codex\skills\daily-report\scripts\render_project_report.py' --report-json 'D:\lijingSun\Doc\周报日报\YYMMDD日报\YYMMDD日报.json' --output-dir 'D:\lijingSun\Doc\周报日报\YYMMDD日报'
  ```

- Keep the HTML and Markdown body in the same three-part project order, with date/cutoff metadata above it. Do not manually add a standalone tomorrow-plan chapter. The four Feishu fields (`今日总结`, `今日对接客户名称`, `明日计划`, `需要协调与帮助`) are derived from the same confirmed JSON by the report renderer, retaining the distinction between a dated tomorrow action and an undated follow-up; do not hand-edit them into a conflicting report.
- Put copy-ready Markdown in a fenced `text` block when showing it in chat.
- When revising a report, update JSON first and regenerate both outputs; never patch only one derivative.
- After all local files pass delivery checks, import the confirmed canonical JSON into the star workbench database using [`references/workbench-input.md`](references/workbench-input.md). Then **must execute** the standing Feishu archive sync in [`references/feishu-archive-sync.md`](references/feishu-archive-sync.md). A workbench import failure must be reported and retried separately; it does not waive the Feishu sync. The sync is not optional merely because no Feishu MCP connector appears in the current tool list: first check for the locally installed `lark-cli` command and use it when available. Report delivery is incomplete until the configured Feishu report and attachment folders have been synchronized, or a concrete authentication/permission/upload failure has been recorded after retrying safe alternatives.
- After a confirmed report has passed the local checks and the Feishu archive sync has succeeded, read [`references/feishu-report-submit.md`](references/feishu-report-submit.md) and run [`scripts/feishu_report_submit.py`](scripts/feishu_report_submit.py) with `--submit`. The script must run headlessly, use the saved Feishu storage state, process only `今日总结`, `今日对接客户名称`, `明日计划`, and `需要协调与帮助`, and leave reporter, CC recipients, forwarding, and OKR controls unchanged. It must stop on an expired deadline, an already-submitted report, an invalid login state, missing archive manifest, missing editor, or any failed pre-submit content check. Never submit based only on a changed URL; require the visible `提交成功` result and retain the execution log.

## Delivery checks

Before delivery, verify:

- every yesterday commitment has an explicit outcome;
- every yesterday commitment displays `是否已完成` and a factual reason;
- every actual-work item displays `是否进行`, current progress, today's change, result/validation, and known blocker, coordination, and next action in its project or `其他工作与备注` group;
- `projects[]` uses only confirmed project IDs, `related_project_ids` creates no duplicate item/count, and project-level plans appear at the related project group's end;
- pure `notes[]` do not count as results or mutate tasks; `decisions[]` preserves confirmed versus proposed status and known sources;
- every unfinished item preserves its known next action; optional dates are included only when supplied, otherwise null/omitted and hidden in rendered output;
- every temporary addition has a reason;
- the same item keeps the same ID across daily and weekly sources;
- every daily item has a valid `parent_item_id` or an explicit null mapping;
- no daily item is silently merged, dropped, or remapped without a recorded reason;
- today's workbench status events and plan-linked notes are represented once even when their plan date is earlier; each adopted note keeps its source entry ID;
- execution, validation, and schedule statuses do not contradict each other;
- canonical JSON declares `report_layout: "project-v1"` and `workbench_schema_version: 2`; HTML, Markdown, and Feishu's four text fields represent the same facts and follow-up date semantics;
- HTML and Markdown contain exactly the three main report parts, without an independent tomorrow-plan, defect, test, or coordination chapter;
- all supplied local links resolve inside the report folder;
- no facts, metrics, dates, or evidence were invented.
- when Feishu archive sync is configured, its manifest records the native Markdown, HTML, and every confirmed attachment in their configured folders; when configuration is incomplete, local report delivery succeeds and the sync blocker is stated explicitly.
