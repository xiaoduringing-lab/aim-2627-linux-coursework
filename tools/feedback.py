"""Console feedback shared by local tests and GitHub Actions logs."""


def execution_status(code):
    if code == 0:
        return "PASS", "执行成功"
    if code == 77:
        return "SKIP", "尚未实现，记 0 分"
    if code == 124:
        return "FAIL", "超过 15 秒执行限制"
    if code < 0:
        return "FAIL", f"被信号 {-code} 终止"
    return "FAIL", f"退出状态 {code}"


def execution_lines(record, verbose=False):
    tag, explanation = execution_status(record["exit_code"])
    attempt = record.get("attempt", 1)
    action = record.get("action", "run")
    stage = f"第 {attempt} 次运行" if action == "run" else f"{action}（第 {attempt} 次调用）"
    lines = [f"  [{tag}] 场景 {record['case']} / {stage}：{explanation}"]
    if record["exit_code"] not in (0, 77) or verbose:
        lines.append(f"    脚本：src/main/{record['script']}")
        for key in ("stdout", "stderr"):
            value = record.get(key, "")
            if value:
                suffix = "（末尾 4000 字符，已截断）" if record.get(key + "_truncated") else ""
                lines.append(f"    {key}{suffix}：")
                lines.extend("      " + line for line in value.rstrip("\n").splitlines())
            elif record["exit_code"] not in (0, 77):
                lines.append(f"    {key}：（空）")
    return lines


def question_lines(result, cases):
    lines = []
    for case in cases:
        if case.error is not None:
            lines.append(f"  [场景失败] {case.name}：准备或脚本执行未完成")
            lines.extend("    " + line for line in str(case.error).splitlines())
    tags = {"passed": "PASS", "failed": "FAIL", "pending": "SKIP"}
    for check in result["checks"]:
        lines.append(f"  [{tags[check['status']]}] {check['name']}：{check['points']}/{check['max_points']}")
        for item in check.get("cases", []):
            if item["status"] == "failed":
                if item.get("stage") == "execution":
                    lines.append(f"    {item['case']}：场景执行失败，见上方退出状态和错误信息")
                else:
                    lines.append(f"    {item['case']}：")
                    lines.extend("      " + line for line in item["message"].splitlines())
        if check["status"] == "pending":
            lines.append("    未实现的场景跳过检查，记 0 分")
    lines.append(f"  结果：{result['status']}，{result['points']}/{result['max_points']}\n")
    return lines
