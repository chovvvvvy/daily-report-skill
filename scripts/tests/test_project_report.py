import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from render_project_report import render, build_feishu_fields, validate
from feishu_report_submit import build_fields, SubmissionError


def item(identity, project, title, **extra):
    return dict(item_id=identity, project_id=project, title=title,
                source_type="carried_daily", parent_item_id=None,
                yesterday_commitment="完成对接验证", commitment_fulfilled="否",
                commitment_reason="测试环境暂不可用", progress_status="是",
                progress_summary="接口已对齐，等待联调", today_delta="补齐错误处理",
                execution_status="进行中", validation_status="待验证", schedule_status="有风险",
                result="本地检查通过，联调未执行", next_action="恢复环境后进行联调", **extra)


def fixture():
    report = {
        "report_layout": "project-v1", "workbench_schema_version": 2,
        "report_date": "2026-10-07", "data_cutoff": "2026-10-07 18:00",
        "generated_at": "2026-10-07 18:05", "overall_status": "测试样例 · 用于验证项目分组，不是实际日报",
        "projects": [{"project_id": "alpha", "name": "示例项目 A", "summary": "接口已对齐，等待联调。"},
                     {"project_id": "beta", "name": "示例项目 B", "summary": "本轮修复已完成，等待验收。"}],
        "items": [item("T-A", "alpha", "接口联调", related_project_ids=["beta"], coordination="请提供测试环境", resume_context={"location": "feature/example 分支的集成测试处"}),
                  item("T-B", "beta", "页面修复"), item("T-C", None, "临时协作支持")],
        "tomorrow_plan": [
            {"item_id": "T-A", "project_id": "alpha", "action": "复测接口", "expected_result": "获得联调结论", "target_date": "2026-10-08", "due_date": "2026-10-12"},
            {"item_id": "T-A", "project_id": "beta", "action": "整理联调资料", "expected_result": "一份对接说明", "target_date": None},
            {"item_id": None, "project_id": "beta", "action": "讨论下一轮范围", "target_date": None},
            {"item_id": "T-C", "project_id": None, "action": "回访协作方", "target_date": "2026-10-10"}],
        "notes": [{"note_id": "N-A", "project_id": "alpha", "body": "考虑增加错误提示，尚未决定执行。"},
                  {"note_id": "N-B", "body": "其他想法：<script>alert(1)</script> 仅作文本。"}],
        "decisions": [{"decision_id": "D-A", "project_id": "alpha", "item_id": "T-A", "status": "proposed", "decision": "考虑增加降级路径", "reason": "减少环境依赖", "impact": "可能调整接口", "source_refs": ["本次批量口述（测试）"]}],
        "coordination": ["协作排期需确认"], "customer_names": [],
    }
    report["items"][1].update(yesterday_commitment="完成页面修复", commitment_fulfilled="是", commitment_reason="页面修复已完成，验收另行安排", progress_status="否", progress_summary="代码修复结束，等待人工验收", today_delta="修复长标题换行", execution_status="已完成", schedule_status="正常", result="页面修复代码已完成，人工验收待进行", next_action="开展人工验收")
    report["items"][2].update(source_type="temporary_addition", yesterday_commitment="不适用", commitment_fulfilled="不适用", commitment_reason="临时增加的协作支持", addition_reason="临时协作请求")
    return report


class ProjectReportTests(unittest.TestCase):
    def test_project_hierarchy_and_plan_placement(self):
        html, md = render(fixture())
        self.assertEqual(html.count('<div class="daily-item">'), 3)
        self.assertIn("关联事项引用", html)
        self.assertLess(md.index("明日安排"), md.index("### 示例项目 B", md.index("## 二、项目推进")))
        self.assertNotIn("## 明日计划", md)
        self.assertIn("讨论中的想法（未确认）", md)
        self.assertIn("其他工作与备注", md)
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("{{report_content}}", html)

    def test_fields_share_facts_and_preserve_schedule(self):
        report = fixture()
        fields = build_fields(report)
        self.assertEqual(fields, build_feishu_fields(report))
        self.assertIn("后续安排（未排期）：整理联调资料", fields["明日计划"])
        self.assertIn("执行日期 · 2026-10-10", fields["明日计划"])
        self.assertIn("截止日期：2026-10-12", fields["明日计划"])
        self.assertIn("是否已完成：否", fields["今日总结"])
        self.assertIn("验证：待验证", fields["今日总结"])
        self.assertIn("请提供测试环境", fields["需要协调与帮助"])
        self.assertNotIn("讨论下一轮范围", fields["今日总结"])

    def test_notes_do_not_become_work_and_input_is_immutable(self):
        report = fixture()
        before = copy.deepcopy(report)
        html, _ = render(report)
        self.assertEqual(report, before)
        self.assertEqual(html.count('<div class="daily-item">'), len(report["items"]))
        self.assertEqual(html.count('考虑增加错误提示'), 1)

    def test_unknown_outcome_stays_unknown(self):
        report = fixture()
        report["items"][0]["commitment_fulfilled"] = "待确认"
        report["items"][0]["progress_status"] = "待确认"
        _, md = render(report)
        self.assertIn("是否已完成：待确认", md)
        self.assertIn("是否进行：待确认", md)

    def test_item_deadline_and_addition_reason_are_not_lost(self):
        report = fixture()
        report["items"][0].update(due_date="2026-10-15", addition_reason="临时请求的对接支持")
        html, md = render(report)
        fields = build_fields(report)
        for output in (html, md, fields["今日总结"]):
            self.assertIn("2026-10-15", output)
            self.assertIn("临时请求的对接支持", output)

    def test_stable_identity_and_explicit_null_project(self):
        report = fixture()
        report["items"][0]["work_item_id"] = "stable-a"
        validate(report)
        report["items"][1]["work_item_id"] = "stable-a"
        with self.assertRaises(ValueError):
            validate(report)
        report = fixture()
        report["tomorrow_plan"][0]["work_item_id"] = "wrong"
        with self.assertRaises(ValueError):
            validate(report)
        report = fixture()
        del report["tomorrow_plan"][0]["project_id"]
        with self.assertRaises(ValueError):
            validate(report)

    def test_bad_references_and_dates_fail_before_writing(self):
        changes = [lambda r: r["items"][0].update(project_id="unknown"),
                   lambda r: r["tomorrow_plan"][0].update(target_date="2026-02-30"),
                   lambda r: r["notes"][0].update(item_id="missing"),
                   lambda r: r["notes"][0].update(item_id="T-C"),
                   lambda r: r["items"].append(copy.deepcopy(r["items"][0])),
                   lambda r: r["decisions"][0].update(status="completed")]
        for mutate in changes:
            report = fixture()
            mutate(report)
            with self.subTest(report=report), self.assertRaises(ValueError):
                validate(report)

    def test_workbench_note_adoption_requires_link(self):
        report = fixture()
        report["notes"][0]["source_entry_ids"] = ["entry-test"]
        with self.assertRaises(ValueError):
            validate(report)
        report["workbench_entry_ids"] = ["entry-test"]
        validate(report)

    def test_unsafe_link_rejected(self):
        report = fixture()
        report["items"][0]["attachments"] = [{"name": "坏链接", "url": "javascript:alert(1)"}]
        with self.assertRaises(ValueError):
            render(report)

    def test_legacy_feishu_unchanged(self):
        report = {"items": [{"title": "旧任务", "today_delta": "处理完成", "result": "本地通过"}],
                  "tomorrow_plan": [{"action": "旧安排", "expected_result": "旧结果"}]}
        fields = build_fields(report)
        self.assertEqual(fields["今日总结"], "1. 旧任务：处理完成；本地通过。")
        self.assertEqual(fields["明日计划"], "1. 旧安排；预期：旧结果。")

    def test_feishu_plain_text_preserves_code_and_punctuation(self):
        report = fixture()
        report["items"][0]["today_delta"] = "核对 bank_* [样本] < 10 的结果"
        fields = build_fields(report)
        self.assertIn(report["items"][0]["today_delta"], fields["今日总结"])

    def test_cli_render_and_prepare_only_offline(self):
        with tempfile.TemporaryDirectory(prefix="report-project-test-") as directory:
            root = Path(directory)
            source = root / "preview.json"
            source.write_text(json.dumps(fixture(), ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPTS / "render_project_report.py"), "--report-json", str(source), "--output-dir", str(root)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "preview.html").is_file())
            self.assertTrue((root / "preview.md").is_file())
            result = subprocess.run([sys.executable, str(SCRIPTS / "feishu_report_submit.py"), "--report-json", str(source), "--prepare-only"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("后续安排", result.stdout)
            self.assertFalse((root / "preview.feishu-submit.json").exists())


if __name__ == "__main__":
    unittest.main()
