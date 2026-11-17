# 按项目组织的日报数据约定

新生成的日报写 `report_layout: "project-v1"`、`workbench_schema_version: 2`。这是展示与可选字段的扩展，继续使用 `items[]` 和 `tomorrow_plan[]`；旧报告按原格式读取，不批量改写。日报、周报和工作台共用稳定事项身份。

## 一次核对

将上一份有效报告的承诺、持续未完事项、相关周计划和当天工作台候选一次按项目列齐。列出源日期、已知事实、待确认结果、项目归属疑问及可选后续安排。用户一次口述，由 Codex 归类；不按项目逐轮询问。可选日期、附件、备注没说就不填，未知事实保留待确认。实质矛盾集中补问，完整整理稿统一确认。

## 规范 JSON

保留 Skill 原有报告时间、事项状态、承诺兑现与来源字段。新增字段如下：

`projects`、`items`、`tomorrow_plan` 必须提供数组，即使为空；每个事项/行动必须显式提供 `project_id`（可 null），行动还必须提供 `item_id`（可 null）。其他可选数组省略即可。`report_layout: project-v1` 仅用于日报；周报保留原数组结构并复用下面的项目归属规则。

| 字段 | 含义 |
|---|---|
| `projects[]` | 本报告涉及的项目目录；每项 `project_id`、`name`，可选 `summary` 为确认后的项目当前状态，不是推断的百分比 |
| `items[].project_id` | 主归属，未明确时为 null；既有项目使用工作台登记 ID |
| `items[].related_project_ids[]` | 明确相关的其他项目；仅引用，一条事项不复制计数 |
| `items[].blocker` / `coordination` | 可选阻碍与协调内容，归在对应事项 |
| `items[].resume_context` | 可选 `{location, references:[{label,url}]}`；记录停在哪里、资料/分支/命令入口，不重复下一步正文 |
| `notes[]` | 纯备注，每条 `{note_id, body, project_id?, item_id?, source_entry_ids?}`；不是任务、成果或承诺 |
| `decisions[]` | `{decision_id, project_id?, item_id?, status, decision, reason?, impact?, source_refs?}`；status 为 `confirmed` 或 `proposed`，来源为字符串数组，讨论中的内容不可写成已决定 |

`items[]` 只放真实工作事项，包括未归属项目的其他任务。每项保留原有 `item_id`、`source_type`、`parent_item_id`、`yesterday_commitment`、`commitment_fulfilled`、`commitment_reason`、`progress_status`、`progress_summary`、`today_delta`、`execution_status`、`validation_status`、`schedule_status`、`result`、`next_action`。证据不足的事实显式写 `待确认`；临时新增事项的昨日承诺为不适用并说明原因。缺少可选字段不生成占位。

### 后续安排

- `tomorrow_plan[]` 是兼容已有接口的字段名，不表示所有行动都是明天。每项使用 `action`、`expected_result`、`item_id`、`project_id`，可选 `target_date`、`due_date` 及既有来源字段。
- 已属于具体事项的行动保留对应 `item_id`，展示在该事项内部；Codex 在生成时按已确认归属填写 `project_id`，未知显式写 null。
- 只有项目级安排时，`item_id: null`，提供项目 ID，展示在项目末尾。归属未知时项目也可空，进入其他工作与备注。
- `target_date` 是明确执行日；`due_date` 是最晚完成日，两者独立。明确“明天”按报告日期换算。没有日期就留空，显示“后续安排”，不进入工作台今日计划。
- `next_action` 是同一份确认事实的简洁描述，`tomorrow_plan[]` 保存需跟踪的具体行动；Codex 一次整理，同源维护。只写下一步文字不会让程序自动新建行动。
- 保留稳定 `item_id` / 可选 `work_item_id`，不靠标题合并；同一报告中最终身份 `work_item_id || item_id` 不得重复。项目级计划没有事项编号时只保存计划，不提供 `work_item_id`，不新建伪事项卡片。

### 项目归属与引用

- 已关联的项目必须出现在本报告 `projects` 目录且已登记到工作台；目录不是自动注册命令。新项目登记遵循现有 CLI 流程。
- 未确定归属的旧条目保留 null，在一次核对中列出；不能从“服务器部署”等宽泛标题猜归属。
- 一个事项在报告中只出现一个主体。相关项目通过引用可发现该事项，不重复计算成果。
- 事项主归属优先；历史或明确跨项目行动保留各自项目关系，展示时标注行动项目，不覆盖事项归属。新版显式 null 保持未归属；仅旧格式没有该字段时可沿用唯一明确行动项目，多个项目时保持未归属。
- 项目分组不是重新编号或拆分依据。历史合并事项要拆分，先确认范围及映射，不能自动拆旧 ID。
- 备注或决策若给出 `item_id`，必须指向本报告事项；给出的项目必须属于该事项主项目或相关项目。无事项编号时直接归项目或其他备注。

## 展示与输出

日报正文只有三个主部分：

1. 昨日承诺兑现：按项目，每个事项独立展示承诺、是否完成、事实原因；临时新增标记不适用。
2. 项目推进：项目标题及可选一句话摘要 → 事项 → 当前进程、今日变化、结果与独立验证状态 → 阻碍/协调（有才展示）→ 下一步与安排 → 资料。只有项目级安排的放项目末尾。决策和备注在对应事项或项目下。
3. 其他工作与备注：无主项目的真实任务、无归属行动和纯备注，明确区分记录性质。

缺陷、测试、协调进入对应事项，不再另设五个章节；不单列明日计划章节。HTML、Markdown 使用相同结构。没有日报记录的项目不自动宣称当日有进展。

确定性生成：

```powershell
& 'C:\Users\eqy\.codex\report-sync\.venv\Scripts\python.exe' 'C:\Users\eqy\.codex\skills\daily-report\scripts\render_project_report.py' --report-json '<已确认JSON>' --output-dir '<该日报文件夹>'
```

该命令只读取 JSON、生成同名 HTML/Markdown，不调用模型、不写数据库、不上传。输入的 JSON 由 Codex 与用户确认后生成；预览测试只使用隔离目录。

飞书四个固定字段保持：今日总结由同一报告事实生成（包含承诺核对和项目进展），明日计划汇总关联行动并明确标注“明日安排／后续安排／执行日期”，客户与协调只用确认内容。表单结构不同，事实必须一致；未来安排不计今日成果。`--prepare-only` 只核对字段，不提交。

## 工作台与周报

- 工作台继续导入 `items[]`、`tomorrow_plan[]`。`notes[]`、`decisions[]` 保留在报告快照，不自动转换为任务、行动或工作日志；原文入口可查看。纯备注转为任务须用户明确确认后写入 `items[]`。
- 采用备注的 `source_entry_ids` 时，同步加入现有顶层 `workbench_entry_ids`，让原接口记录采用关系；只有来自 candidate.entries 的真实 ID 才能使用。决策来源不冒充 journal entry ID。
- 手动状态覆盖仍需精确 `workbench_task_revision`。重导不能重复建卡或重复统计，排序事件和想法不是工作成果。
- 周报保留既有上周问题汇总、本周关键成果、下周计划三章；各章内按项目聚合，按持续事项身份合并各日日志，明日安排只提供计划线索。相关项目引用不重复计数。
- 工作台只读取结构化数据和保存用户操作，不调用大模型。项目版本推进仍以登记的迭代文档为权威来源。
