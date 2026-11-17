#!/usr/bin/env python3
"""Render confirmed project-v1 daily JSON; no model, database, or network calls."""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

LAYOUT = "project-v1"
TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "daily-report-template.html"


def text(value):
    return "" if value is None else str(value).strip()


def values(report, key):
    value = report.get(key, [])
    if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
        raise ValueError(f"{key} 必须是对象数组")
    return value


def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"无效日期：{value}")
    return date.fromisoformat(value)


def validate(report):
    if report.get("report_layout") != LAYOUT or report.get("workbench_schema_version") != 2:
        raise ValueError("新日报须声明 report_layout:project-v1 和 workbench_schema_version:2")
    valid_date(report.get("report_date"))
    for key in ("projects", "items", "tomorrow_plan"):
        if key not in report:
            raise ValueError(f"新日报必须提供 {key} 数组（可为空）")
    projects = values(report, "projects")
    project_ids = [p.get("project_id") for p in projects]
    if any(not isinstance(p, str) or not p.strip() for p in project_ids) or len(set(project_ids)) != len(project_ids):
        raise ValueError("项目 ID 必须非空且唯一")
    if any(not text(p.get("name")) for p in projects):
        raise ValueError("项目名称不能为空")
    items = values(report, "items")
    ids = [i.get("item_id") for i in items]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("事项 ID 必须非空且唯一")
    stable_ids = [i.get("work_item_id") or i["item_id"] for i in items]
    if any(not isinstance(i, str) or not i.strip() for i in stable_ids) or len(set(stable_ids)) != len(stable_ids):
        raise ValueError("持续事项身份重复或无效")
    required = ("title", "commitment_reason", "progress_summary", "today_delta", "result", "next_action")
    enums = {
        "commitment_fulfilled": {"是", "否", "不适用", "待确认"},
        "progress_status": {"是", "否", "待确认"},
        "execution_status": {"待确认", "未开始", "进行中", "已完成", "阻塞", "取消"},
        "validation_status": {"待确认", "无需验证", "待验证", "已通过", "未通过"},
        "schedule_status": {"待确认", "正常", "有风险", "已延期"},
    }
    for i in items:
        if any(not text(i.get(k)) for k in required):
            raise ValueError(f"事项 {i['item_id']} 缺少事实字段；未知事实显式填待确认")
        for key, allowed in enums.items():
            if i.get(key) not in allowed:
                raise ValueError(f"事项 {i['item_id']} 的 {key} 无效")
        related = i.get("related_project_ids", [])
        if not isinstance(related, list) or any(not isinstance(p, str) for p in related) or len(set(related)) != len(related):
            raise ValueError("related_project_ids 必须是唯一项目 ID 数组")
        if i.get("project_id") in related:
            raise ValueError("相关项目不应重复主项目")
        for p in related:
            if p not in project_ids:
                raise ValueError(f"相关项目未在报告声明：{p}")
    by_id = {i["item_id"]: i for i in items}
    for key in ("items", "tomorrow_plan", "notes", "decisions"):
        seen = set()
        for obj in values(report, key):
            if key in ("items", "tomorrow_plan") and "project_id" not in obj:
                raise ValueError(f"{key} 必须显式给出 project_id，可为 null")
            if key == "tomorrow_plan" and "item_id" not in obj:
                raise ValueError("行动必须显式给出 item_id，可为 null")
            p = obj.get("project_id")
            if p is not None and p not in project_ids:
                raise ValueError(f"{key} 项目未在报告声明：{p}")
            item_id = obj.get("item_id")
            if key != "items" and item_id is not None and item_id not in by_id:
                raise ValueError(f"{key} 引用不存在的事项：{item_id}")
            if key in ("notes", "decisions"):
                id_key = "note_id" if key == "notes" else "decision_id"
                identity = obj.get(id_key)
                if not isinstance(identity, str) or not identity.strip() or identity in seen:
                    raise ValueError(f"{key} 编号必须非空且唯一")
                seen.add(identity)
                if not text(obj.get("body" if key == "notes" else "decision")):
                    raise ValueError(f"{key} 正文不能为空")
                if item_id and p is not None and p not in [by_id[item_id].get("project_id"), *by_id[item_id].get("related_project_ids", [])]:
                    raise ValueError(f"{key} 与事项的项目关联冲突")
            if key == "decisions" and obj.get("status") not in ("confirmed", "proposed"):
                raise ValueError("决策须标明 confirmed 或 proposed")
            if key == "tomorrow_plan" and not text(obj.get("action")):
                raise ValueError("行动内容不能为空")
            if key == "tomorrow_plan" and not item_id and obj.get("work_item_id"):
                raise ValueError("项目级行动不能提供独立的 work_item_id")
            if key == "tomorrow_plan" and item_id and obj.get("work_item_id") and obj["work_item_id"] != (by_id[item_id].get("work_item_id") or item_id):
                raise ValueError("行动持续事项身份与关联事项不一致")
            for field in ("target_date", "due_date"):
                if obj.get(field) is not None:
                    valid_date(obj[field])
    # A note adopted from the workbench uses the existing report-level linking API.
    adopted = set(report.get("workbench_entry_ids", []))
    for note in values(report, "notes"):
        if any(entry not in adopted for entry in note.get("source_entry_ids", [])):
            raise ValueError("备注 source_entry_ids 须同时加入 workbench_entry_ids")


def markdown_text(value):
    return re.sub(r"([\\`*_\[\]<>#|])", r"\\\1", text(value)).replace("\n", "  \n")


def safe_url(value):
    url = text(value)
    if not url:
        return ""
    # Drive-letter paths are local resources, never executable URL schemes.
    if re.match(r"^[A-Za-z]:[\\/]", url):
        return Path(url).as_uri()
    if urlsplit(url).scheme.lower() not in ("", "https", "http", "file", "obsidian"):
        raise ValueError("资料链接协议不支持")
    return url


class Document:
    def __init__(self):
        self.html = []
        self.md = []
        self.plain = []

    def open(self, cls):
        self.html.append(f'<div class="{cls}">')

    def close(self):
        self.html.append("</div>")

    def heading(self, level, value):
        self.html.append(f"<h{level}>{escape(text(value))}</h{level}>")
        self.md.append("#" * level + " " + markdown_text(value))
        self.plain.append(text(value))

    def paragraph(self, value, label=None):
        if not text(value):
            return
        prefix = f"{label}：" if label else ""
        self.html.append("<p>" + (f"<strong>{escape(prefix)}</strong>" if prefix else "") + escape(text(value)).replace("\n", "<br>") + "</p>")
        self.md.append(markdown_text(prefix + text(value)))
        self.plain.append(prefix + text(value))

    def link(self, label, url, description=""):
        url = safe_url(url)
        if not url:
            self.paragraph(label)
        else:
            self.html.append(f'<p><a href="{escape(url, quote=True)}">{escape(text(label))}</a></p>')
            self.md.append(f"[{markdown_text(label)}](<{url.replace('>', '%3E').replace('<', '%3C')}>)")
            self.plain.append(f"{text(label)}：{url}")
        self.paragraph(description)


def plan_label(plan, report_date):
    target = plan.get("target_date")
    tomorrow = (valid_date(report_date) + timedelta(days=1)).isoformat()
    if not target:
        return "后续安排（未排期）"
    return f"明日安排 · {target}" if target == tomorrow else f"执行日期 · {target}"


def project_name(report, project_id):
    return next((p["name"] for p in report.get("projects", []) if p["project_id"] == project_id), "其他工作／归属待确认")


def render_annotations(doc, report, item_id, project_id):
    for key in ("decisions", "notes"):
        for obj in report.get(key, []):
            if obj.get("item_id") != item_id or (item_id is None and obj.get("project_id") != project_id):
                continue
            if key == "notes":
                doc.paragraph(obj["body"], "备注")
            else:
                doc.paragraph(obj["decision"], "已确认决策／需求变化" if obj["status"] == "confirmed" else "讨论中的想法（未确认）")
                doc.paragraph(obj.get("reason"), "原因")
                doc.paragraph(obj.get("impact"), "影响")
                for source in obj.get("source_refs", []):
                    doc.paragraph(source, "来源")


def render_plan(doc, report, plan, context_project):
    doc.paragraph(plan["action"], plan_label(plan, report["report_date"]))
    doc.paragraph(plan.get("expected_result"), "预期结果")
    if plan.get("project_id") and plan["project_id"] != context_project:
        doc.paragraph(project_name(report, plan["project_id"]), "行动关联项目")
    if plan.get("due_date"):
        doc.paragraph(plan["due_date"], "截止日期")


def render_item(doc, report, item, include_plans):
    doc.open("daily-item")
    doc.open("narrative")
    doc.heading(4, item["title"])
    doc.paragraph(item["item_id"], "事项编号")
    doc.paragraph(" · ".join(f"{label}：{item[key]}" for label, key in (("执行", "execution_status"), ("验证", "validation_status"), ("排期", "schedule_status"))))
    doc.paragraph(item["progress_status"], "是否进行")
    doc.paragraph(item["progress_summary"], "当前进程")
    doc.paragraph(item["today_delta"], "今日变化")
    doc.paragraph(item["result"], "结果")
    doc.paragraph(item.get("addition_reason"), "临时新增原因")
    if item.get("due_date"):
        doc.paragraph(item["due_date"], "事项截止日期")
    doc.paragraph(item.get("blocker"), "阻碍")
    doc.paragraph(item.get("coordination"), "需要协调")
    doc.paragraph(item["next_action"], "下一步")
    if item.get("related_project_ids"):
        doc.paragraph("、".join(project_name(report, p) for p in item["related_project_ids"]), "相关项目（同一事项）")
    context = item.get("resume_context") or {}
    doc.paragraph(context.get("location"), "继续工作入口")
    for ref in context.get("references", []):
        doc.link(ref.get("label") or ref.get("url"), ref.get("url"))
    if include_plans:
        for plan in report.get("tomorrow_plan", []):
            if plan.get("item_id") == item["item_id"]:
                render_plan(doc, report, plan, item.get("project_id"))
    render_annotations(doc, report, item["item_id"], item.get("project_id"))
    doc.close()
    doc.open("attachment")
    doc.paragraph("附件")
    attachments = item.get("attachments") or []
    if not attachments:
        doc.paragraph("无")
    for a in attachments:
        if isinstance(a, str):
            doc.link(a, a)
        else:
            doc.link(a.get("name") or a.get("label") or "资料", a.get("relative_path") or a.get("url") or a.get("path"), a.get("description") or a.get("evidence_summary"))
    doc.close()
    doc.close()


def render(report, include_plans=True, plain_text=False):
    validate(report)
    doc = Document()
    doc.heading(1, f"工作日报 · {report['report_date']}")
    doc.paragraph(report.get("data_cutoff"), "数据截至")
    doc.paragraph(report.get("generated_at"), "生成时间")
    doc.paragraph(report.get("overall_status"), "今日概况")
    groups = [(p["project_id"], p["name"]) for p in report.get("projects", [])] + [(None, "其他工作／归属待确认")]
    doc.open("section")
    doc.heading(2, "一、昨日承诺兑现")
    for pid, name in groups:
        items = [i for i in report.get("items", []) if i.get("project_id") == pid]
        if not items:
            continue
        doc.heading(3, name)
        for item in items:
            doc.open("commitment-row")
            doc.heading(4, item["title"])
            doc.paragraph(item.get("yesterday_commitment") or ("不适用" if item["commitment_fulfilled"] == "不适用" else "待确认"), "原承诺")
            doc.paragraph(item["commitment_fulfilled"], "是否已完成")
            doc.paragraph(item["commitment_reason"], "事实原因")
            doc.close()
    if not report.get("items"):
        doc.paragraph("本报告没有事项记录，不能据此判断昨日承诺已完成。")
    doc.close()
    doc.open("section")
    doc.heading(2, "二、项目推进")
    for project in report.get("projects", []):
        pid = project["project_id"]
        doc.open("project")
        doc.heading(3, project["name"])
        doc.paragraph(project.get("summary"))
        for item in report.get("items", []):
            if item.get("project_id") == pid:
                render_item(doc, report, item, include_plans)
            elif pid in item.get("related_project_ids", []):
                doc.paragraph(f"{item['title']}（{item['item_id']}），主体见{project_name(report, item.get('project_id'))}。", "关联事项引用")
        if include_plans:
            for plan in report.get("tomorrow_plan", []):
                if plan.get("item_id") is None and plan.get("project_id") == pid:
                    render_plan(doc, report, plan, pid)
        render_annotations(doc, report, None, pid)
        doc.close()
    if not report.get("projects"):
        doc.paragraph("本报告没有明确归属项目的内容。")
    doc.close()
    doc.open("section")
    doc.heading(2, "三、其他工作与备注")
    for item in report.get("items", []):
        if item.get("project_id") is None:
            render_item(doc, report, item, include_plans)
    if include_plans:
        for plan in report.get("tomorrow_plan", []):
            if plan.get("item_id") is None and plan.get("project_id") is None:
                render_plan(doc, report, plan, None)
    render_annotations(doc, report, None, None)
    coordination = report.get("coordination")
    if isinstance(coordination, list):
        for c in coordination:
            doc.paragraph(c, "其他协调事项")
    elif coordination:
        doc.paragraph(coordination, "其他协调事项")
    doc.close()
    template = TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("{{report_title}}", escape(f"工作日报 · {report['report_date']}"))
    html = html.replace("{{report_content}}", "\n".join(doc.html))
    return html, "\n\n".join(doc.plain if plain_text else doc.md) + "\n"


def build_feishu_fields(report):
    _, summary = render(report, include_plans=False, plain_text=True)
    by_id = {i["item_id"]: i for i in report.get("items", [])}
    plans = []
    for plan in report.get("tomorrow_plan", []):
        item = by_id.get(plan.get("item_id"), {})
        pid = plan.get("project_id") or item.get("project_id")
        line = f"{project_name(report, pid)}｜{plan_label(plan, report['report_date'])}：{plan['action']}"
        if plan.get("expected_result"):
            line += f"；预期结果：{plan['expected_result']}"
        if plan.get("due_date"):
            line += f"；截止日期：{plan['due_date']}"
        plans.append(line)
    coordination = report.get("coordination") or []
    if not isinstance(coordination, list):
        coordination = [coordination]
    coordination = [text(c) for c in coordination if text(c)]
    coordination.extend(f"{project_name(report, i.get('project_id'))}／{i['title']}：{i['coordination']}" for i in report.get("items", []) if text(i.get("coordination")))
    customers = report.get("customer_names") or report.get("customers") or report.get("customer_name")
    if isinstance(customers, list):
        customers = "、".join(text(c) for c in customers if text(c))
    return {"今日总结": summary.strip(), "今日对接客户名称": text(customers) or "无",
            "明日计划": "\n".join(plans) or "无", "需要协调与帮助": "\n".join(dict.fromkeys(coordination)) or "无"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report_json.read_text(encoding="utf-8-sig"))
    html, md = render(report)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for suffix, content in ((".html", html), (".md", md)):
        (args.output_dir / (args.report_json.stem + suffix)).write_text(content, encoding="utf-8")
    print(json.dumps({"html": str(args.output_dir / (args.report_json.stem + ".html")), "markdown": str(args.output_dir / (args.report_json.stem + ".md"))}, ensure_ascii=False))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
