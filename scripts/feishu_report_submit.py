#!/usr/bin/env python3
"""Headless Feishu daily-report form submission from confirmed local JSON."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any


REPORT_URL = (
    "https://oa.feishu.cn/report/record/entry?lang=zh-CN"
    "&open_in_browser=true"
    "&from=miniprogram%3Aminiprogram-native-fusion%3Acli_9d0208a7d1bbd10c"
    "&fromAppLink=true"
)
REPORT_RULE_NAME = "工作日报（生态赋能中心）"
FIELD_ORDER = (
    "今日总结",
    "今日对接客户名称",
    "明日计划",
    "需要协调与帮助",
)
LABEL_SELECTORS = {
    "今日总结": "label[title='今日总结']",
    "今日对接客户名称": "label[title^='今日对接客户名称']",
    "明日计划": "label[title='明日计划']",
    "需要协调与帮助": "label[title='需要协调与帮助']",
}
ROW_XPATH = (
    "xpath=ancestor::div["
    "contains(concat(' ', normalize-space(@class), ' '), ' ud__form__item ')"
    "][1]"
)
DIRECT_EDITOR_XPATH = (
    "xpath=//*[@id='editor-kit-biz-wrapper-edit']"
    "/div[@contenteditable='true']"
)


class SubmissionError(RuntimeError):
    """Base exception for a safely stopped submission."""


class AuthenticationRequired(SubmissionError):
    pass


class DeadlineClosed(SubmissionError):
    pass


class AlreadySubmitted(SubmissionError):
    pass


class SubmissionUnconfirmed(SubmissionError):
    pass


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\u200b", "").split())


def sentence(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    return text if text[-1] in "。！？；" else text + "。"


def join_people(value: Any) -> str:
    if isinstance(value, list):
        names = [normalize_text(item) for item in value]
        return "、".join(item for item in names if item) or "无"
    return normalize_text(value) or "无"


def build_fields(report: dict[str, Any]) -> dict[str, str]:
    summary_lines: list[str] = []
    for item in report.get("items") or []:
        if not isinstance(item, dict):
            continue
        title = normalize_text(item.get("title")) or "未命名事项"
        progress = normalize_text(item.get("today_delta"))
        if not progress:
            progress = normalize_text(item.get("progress_summary"))
        result = normalize_text(item.get("result"))
        details = [part for part in (progress, result) if part]
        if details:
            deduplicated = list(dict.fromkeys(details))
            summary_lines.append(
                f"{len(summary_lines) + 1}. {title}："
                + "；".join(deduplicated)
                + "。"
            )

    if not summary_lines:
        overall = normalize_text(report.get("overall_status"))
        if overall:
            summary_lines.append(sentence(overall))

    customers = join_people(
        report.get("customer_names")
        or report.get("customers")
        or report.get("customer_name")
    )

    tomorrow_lines: list[str] = []
    for entry in report.get("tomorrow_plan") or []:
        if isinstance(entry, dict):
            action = normalize_text(entry.get("action"))
            expected = normalize_text(entry.get("expected_result"))
            if action:
                line = f"{len(tomorrow_lines) + 1}. {action}"
                if expected:
                    line += f"；预期：{expected}"
                tomorrow_lines.append(sentence(line))
        else:
            text = normalize_text(entry)
            if text:
                tomorrow_lines.append(sentence(text))
    if not tomorrow_lines:
        tomorrow_lines.append("无")

    coordination = report.get("coordination")
    if isinstance(coordination, list):
        coordination_lines = [normalize_text(item) for item in coordination]
        coordination_text = "\n".join(item for item in coordination_lines if item)
    else:
        coordination_text = normalize_text(coordination)

    fields = {
        "今日总结": "\n".join(summary_lines),
        "今日对接客户名称": customers,
        "明日计划": "\n".join(tomorrow_lines),
        "需要协调与帮助": coordination_text or "无",
    }
    missing = [label for label in FIELD_ORDER if not normalize_text(fields[label])]
    if missing:
        raise SubmissionError("生成后仍为空的字段: " + "、".join(missing))
    return fields


def validate_archive_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SubmissionError(f"飞书归档清单不存在: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    files = manifest.get("files") or []
    kinds = {
        item.get("kind")
        for item in files
        if isinstance(item, dict) and item.get("file_token")
    }
    missing = {"markdown", "html"} - kinds
    if missing:
        raise SubmissionError(
            "飞书归档未完成，清单缺少成功对象: " + ", ".join(sorted(missing))
        )
    if not manifest.get("synced_at"):
        raise SubmissionError("飞书归档清单缺少 synced_at")
    return manifest


class ExecutionRecorder:
    def __init__(
        self,
        path: Path,
        report_json: Path,
        archive_manifest: Path | None,
        report_date: str,
    ) -> None:
        self.path = path
        self.payload: dict[str, Any] = {
            "report_date": report_date,
            "report_json": str(report_json),
            "archive_manifest": str(archive_manifest) if archive_manifest else None,
            "status": "running",
            "events": [],
        }
        self.write()

    def record(self, step: str, status: str = "ok", detail: str = "") -> None:
        self.payload["events"].append(
            {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "step": step,
                "status": status,
                "detail": detail,
            }
        )
        self.write()

    def finish(self, status: str, detail: str = "") -> None:
        self.payload["status"] = status
        self.payload["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if detail:
            self.payload["detail"] = detail
        self.write()

    def write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def resolve_editor(page: Any, label: str, timeout_ms: int) -> Any:
    label_locator = page.locator(LABEL_SELECTORS[label])
    if label_locator.count() != 1:
        raise SubmissionError(
            f"字段标签数量异常: {label}={label_locator.count()}"
        )
    row = label_locator.locator(ROW_XPATH)
    editor = row.locator("[contenteditable='true']")
    if editor.count() != 1:
        raise SubmissionError(f"字段编辑器数量异常: {label}={editor.count()}")
    editor.wait_for(state="visible", timeout=timeout_ms)
    return editor


def open_report_form(page: Any, timeout_ms: int, recorder: ExecutionRecorder) -> None:
    page.goto(REPORT_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    if "accounts.feishu.cn" in page.url:
        raise AuthenticationRequired("飞书登录态已失效")
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    recorder.record("打开汇报看板")

    write_button = page.locator(
        "xpath=//button[contains(normalize-space(.),'写汇报')]"
    )
    write_button.wait_for(state="visible", timeout=timeout_ms)
    write_button.click()
    recorder.record("点击写汇报")

    card_xpath = (
        "//div[contains(@class,'ud__modal') and "
        "contains(@class,'write-report-modal')]"
        f"//*[normalize-space(.)='{REPORT_RULE_NAME}']"
        "/ancestor::div[contains(@class,'index__card__')][1]"
    )
    card = page.locator("xpath=" + card_xpath)
    card.wait_for(state="visible", timeout=timeout_ms)
    card_text = normalize_text(card.inner_text())
    if "已提交" in card_text:
        raise AlreadySubmitted("当前周期日报已经提交")
    card.click()
    recorder.record("选择工作日报规则")

    first_label = page.locator(LABEL_SELECTORS[FIELD_ORDER[0]])
    try:
        first_label.wait_for(state="visible", timeout=timeout_ms)
    except Exception as exc:
        body_text = normalize_text(page.locator("body").inner_text())
        if "截止后无法补交" in body_text or "已超过提交截止" in body_text:
            raise DeadlineClosed("当前日报已超过提交截止时间") from exc
        if "已提交" in body_text:
            raise AlreadySubmitted("当前周期日报已经提交") from exc
        raise SubmissionError("进入日报规则后未出现可填写表单") from exc

    direct_editors = page.locator(DIRECT_EDITOR_XPATH)
    if direct_editors.count() != len(FIELD_ORDER):
        raise SubmissionError(
            f"全页富文本编辑器数量异常: {direct_editors.count()}，预期 {len(FIELD_ORDER)}"
        )
    recorder.record("检查表单结构", detail="4 个富文本编辑器已就绪")


def enter_and_verify_fields(
    page: Any,
    fields: dict[str, str],
    timeout_ms: int,
    recorder: ExecutionRecorder,
) -> None:
    for label in FIELD_ORDER:
        expected = fields[label]
        editor = resolve_editor(page, label, timeout_ms)
        editor.click()
        editor.press("Control+A")
        page.keyboard.insert_text(expected)
        page.wait_for_timeout(200)
        actual = editor.inner_text()
        if normalize_text(actual) != normalize_text(expected):
            raise SubmissionError(f"字段写入校验不一致: {label}")
        recorder.record(
            "填写字段",
            detail=f"{label} 写入一致且非空，字符数 {len(normalize_text(actual))}",
        )

    for label in FIELD_ORDER:
        editor = resolve_editor(page, label, timeout_ms)
        actual = normalize_text(editor.inner_text())
        expected = normalize_text(fields[label])
        if not actual or actual != expected:
            raise SubmissionError(f"提交前最终校验失败: {label}")
    recorder.record("提交前文本框校验", detail="4 个文本框非空且与预期一致")


def submit_and_confirm(page: Any, timeout_ms: int, recorder: ExecutionRecorder) -> None:
    button = page.get_by_role("button", name="提交", exact=True)
    if button.count() != 1:
        raise SubmissionError(f"提交按钮数量异常: {button.count()}")
    button.wait_for(state="visible", timeout=timeout_ms)
    if not button.is_enabled():
        raise SubmissionError("提交按钮不可用")
    recorder.record("提交前按钮校验", detail="提交按钮可见且可用")
    button.click()
    recorder.record("点击提交")
    try:
        page.get_by_text("提交成功", exact=False).wait_for(
            state="visible", timeout=timeout_ms
        )
    except Exception as exc:
        raise SubmissionUnconfirmed("未检测到『提交成功』提示") from exc
    recorder.record("提交结果校验", detail="检测到提交成功提示")


def parse_args() -> argparse.Namespace:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-json", required=True, type=Path)
    parser.add_argument("--archive-manifest", type=Path)
    parser.add_argument(
        "--storage-state",
        type=Path,
        default=skill_root / "feishu_storage_state.json",
    )
    parser.add_argument("--execution-log", type=Path)
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--headed", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--submit", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_json = args.report_json.resolve()
    if not report_json.is_file():
        raise SubmissionError(f"日报 JSON 不存在: {report_json}")
    report = json.loads(report_json.read_text(encoding="utf-8-sig"))
    fields = build_fields(report)

    if args.prepare_only:
        print(json.dumps(fields, ensure_ascii=False, indent=2))
        return 0

    archive_manifest = (
        args.archive_manifest.resolve()
        if args.archive_manifest
        else report_json.with_name(report_json.stem + ".feishu.json")
    )
    validate_archive_manifest(archive_manifest)

    storage_state = args.storage_state.resolve()
    if not storage_state.is_file():
        raise AuthenticationRequired(
            f"无头提交缺少登录态文件: {storage_state}"
        )

    execution_log = (
        args.execution_log.resolve()
        if args.execution_log
        else report_json.with_name(report_json.stem + ".feishu-submit.json")
    )
    artifacts_dir = (
        args.artifacts_dir.resolve()
        if args.artifacts_dir
        else report_json.parent
    )
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    stem = report_json.stem
    recorder = ExecutionRecorder(
        execution_log,
        report_json,
        archive_manifest,
        normalize_text(report.get("report_date")),
    )
    recorder.record("检查飞书归档", detail="Markdown 与 HTML 均已上传")
    recorder.record(
        "生成提交字段",
        detail="；".join(f"{label}:{len(normalize_text(fields[label]))}" for label in FIELD_ORDER),
    )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        recorder.finish("failed", "未安装 playwright")
        raise SubmissionError("未安装 playwright") from exc

    browser = None
    page = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=not args.headed,
                args=["--no-proxy-server", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                storage_state=str(storage_state),
                viewport={"width": 1440, "height": 1000},
            )
            page = context.new_page()
            page.set_default_timeout(args.timeout_ms)
            open_report_form(page, args.timeout_ms, recorder)
            enter_and_verify_fields(page, fields, args.timeout_ms, recorder)
            before = artifacts_dir / f"{stem}.feishu-before-submit.png"
            page.screenshot(path=str(before), full_page=True)
            recorder.record("保存提交前截图", detail=str(before))
            submit_and_confirm(page, args.timeout_ms, recorder)
            after = artifacts_dir / f"{stem}.feishu-after-submit.png"
            page.screenshot(path=str(after), full_page=True)
            recorder.record("保存提交后截图", detail=str(after))
            recorder.finish("submitted", "提交成功")
            browser.close()
            return 0
    except AlreadySubmitted as exc:
        recorder.finish("already_submitted", str(exc))
        if browser:
            browser.close()
        return 0
    except DeadlineClosed as exc:
        recorder.finish("blocked_deadline", str(exc))
        if page:
            page.screenshot(
                path=str(artifacts_dir / f"{stem}.feishu-deadline.png"),
                full_page=True,
            )
        if browser:
            browser.close()
        return 4
    except Exception as exc:
        recorder.record("执行失败", "failed", str(exc))
        recorder.finish("failed", str(exc))
        if page:
            try:
                page.screenshot(
                    path=str(artifacts_dir / f"{stem}.feishu-error.png"),
                    full_page=True,
                )
            except Exception:
                pass
        if browser:
            browser.close()
        return 2


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        raise SystemExit(main())
    except SubmissionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
