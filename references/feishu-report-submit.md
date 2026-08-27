# 飞书日报自动提交流程

用于在日报本地事实源确认、HTML/Markdown 飞书归档上传成功后，自动提交「工作日报（生态赋能中心）」。

## 触发条件

只在以下条件同时满足时执行：

1. 用户已确认日报事实和四个表单字段内容；
2. `YYMMDD日报.json`、HTML、Markdown 已通过本 skill 的本地交付检查；
3. `YYMMDD日报.feishu.json` 清单存在，且其中 Markdown 与 HTML 都有成功上传返回的 `file_token`；
4. 飞书登录态文件存在并且仍有效。

归档上传失败、登录态失效、当前日报已提交或已经超过填写窗口时，停止提交并记录原因。

## 执行脚本

脚本位于 [`scripts/feishu_report_submit.py`](../scripts/feishu_report_submit.py)，默认无头运行。生产提交流程使用：

```powershell
py C:\Users\eqy\.codex\skills\daily-report\scripts\feishu_report_submit.py `
  --report-json "D:\lijingSun\Doc\周报日报\YYMMDD日报\YYMMDD日报.json" `
  --archive-manifest "D:\lijingSun\Doc\周报日报\YYMMDD日报\YYMMDD日报.feishu.json" `
  --submit
```

`--submit` 是实际外部提交开关；缺少该参数只能使用 `--prepare-only` 输出待填四项，不得通过无头流程直接提交。

登录态默认读取：

```text
C:\Users\eqy\.codex\skills\daily-report\feishu_storage_state.json
```

登录态缺失或失效时不要在无头模式中尝试扫码；由用户重新授权并更新该文件。

## 只处理的字段

脚本只处理下面四个富文本框：

- `今日总结`
- `今日对接客户名称（可录多个，若无填无）`
- `明日计划`
- `需要协调与帮助`

汇报人、抄送人、是否允许他人转发、OKR 和其他控件不点击、不选择、不改写。客户名称和协调字段没有确认内容时分别写入事实源允许的 `无`，不得编造。

页面使用 Slate `contenteditable` 编辑器。脚本必须按原生 `label[title]` 锚定字段行，并用真实键盘输入触发前端状态更新；不能只依赖全页第几个编辑器，也不能把隐藏 `input` 当作编辑器。

## 提交前硬校验

提交前必须全部通过：

- 页面没有出现“截止后无法补交”或“已超过提交截止”；
- 四个字段编辑器均存在且可见；
- 使用 `//*[@id="editor-kit-biz-wrapper-edit"]/div[@contenteditable="true"]` 检查全页编辑器数量为 4；
- 每个字段写入后读取实际 `inner_text`，去除零宽字符和空白后非空；
- 实际文本与生成文本逐字段一致；
- 提交按钮唯一、可见且可用。

只有全部通过才允许点击提交。成功必须以“提交成功”提示为证据；仅 URL 变化不能视为成功。

## 执行记录

默认在日报 JSON 同目录写入：

```text
YYMMDD日报.feishu-submit.json
```

记录归档检查、导航、字段字符数、实际文本校验、提交按钮校验、提交结果和截图路径；不记录日报正文。提交前、提交后和错误/截止状态截图也保存在该日报目录。
