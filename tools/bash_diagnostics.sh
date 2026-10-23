# Loaded through BASH_ENV for the student's Bash script. No grading logic.
# bash -E keeps the error trap active in functions/subshells; the exit status is unchanged.
trap '__aim_failed_status=$?; printf "[Bash 错误] %s:%s，退出状态 %s\n  命令：%s\n" "${BASH_SOURCE[0]##*/}" "$LINENO" "$__aim_failed_status" "$BASH_COMMAND" >&2' ERR
