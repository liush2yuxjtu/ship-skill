# ship skill

`/ship` 把当前 Git 工作安全地送到合并完成，并给出可关闭会话的明确结论。

核心流程：

1. 检查仓库、分支、未提交改动、远端和 secrets 风险；
2. Eve 项目先审计功能 eval 覆盖；缺失时自动补真实 session eval；
3. 运行本地 eval gate；
4. 创建安全分支、提交、推送和 PR/MR；
5. 复用已有 `babysit` skill，或执行内置 merge-ready fallback；
6. 合并、同步默认分支，输出 `Safe to exit`。

## 安装

### 用户级

安装到 Pi、OpenCode、Claude Code、Codex 和 Cursor：

```bash
npx skills add liush2yuxjtu/ship-skill \
  --skill ship \
  --agent pi opencode claude-code codex cursor \
  -g -y
```

### 项目级

在项目根目录运行：

```bash
npx skills add liush2yuxjtu/ship-skill \
  --skill ship \
  --agent pi opencode claude-code codex cursor \
  -y
```

项目级公共入口通常落到 `.agents/skills/ship`；Pi 与 Claude Code 也可获得各自项目入口。

## 使用

```text
/ship
/ship run the fast Eve eval tier first
```

该 skill 会执行真实 Git/远端操作。遇到 force-push、跳过 hooks、疑似 secrets、冲突的合并意图或不安全副作用 eval 时会停止并要求确认。

## Eve eval 行为

存在 Eve 依赖或 agent filesystem，但没有 `evals/` 时，skill 不再跳过：

- 创建 `evals/evals.config.ts`；
- 为改动行为创建真实 session-based eval；
- 先运行新增窄 eval，再运行项目 PR gate；
- payment/refund/delete/send 等副作用必须使用 mock、sandbox、dry-run adapter 或专用测试后端，禁止触达生产。

## 验证

```bash
python3 tests/test_skill.py
npx skills add liush2yuxjtu/ship-skill --list
npx skills find ship --owner liush2yuxjtu
```

## License

MIT
