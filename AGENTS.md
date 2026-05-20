# Project Context

<!-- 這個檔案由人和 Archivist 共同維護。Archivist 的任何寫入都必須先經使用者確認。 -->

## Architecture Decisions

<!-- 技術架構選型與重大技術決策。每條一行，指令式，理由括號化。 -->

- Archivist 只做 AGENTS.md 守門員（不做 UI / marketplace / 多 agent）
- AI 負責歸檔判斷，CLI 負責確認後檔案套用
- Codex skill 是主要交付形態；repo install CLI 是輔助模式
- Archivist MVP 完成基線為 Codex skill + CLI helper + templates + tests

## Coding Style

<!-- 程式風格、命名、格式慣例。 -->

## Workflow

<!-- 開發流程、commit / test / deploy 習慣。 -->

- 確認介面固定在 chat；proposed.patch.md 僅作暫存紀錄
- 觸發入口支援 `/Archivist`、`$archivist`、`Archivist sync`；`Archivist sync` 作為 slash fallback

## Tooling

<!-- 套件、工具、環境使用習慣。 -->

- CLI 採單檔 Python 標準函式庫
- `install` 將 Archivist 安裝到目標 repo（建立 `.archivist`、補 AGENTS.md 觸發規則、複製 CLI）
- Skill source 放在 `skills/archivist`，全局安裝版同步到 `~/.codex/skills/archivist`
- `agents/openai.yaml` 使用 `interface:` 區塊，`default_prompt` 必須提到 `$archivist`
- Runtime state 放 `.archivist`（避開 `.codex` sandbox 權限）
- 乾淨初始化模板放 `templates/archivist`
- `SKILL.md` 保持精簡；詳細規則放 `skills/archivist/references/workflow.md`

## Project Rules

<!-- 專案特定規則、約束、不可違反的事項。 -->

- `[!!]` 衝突項不得自動套用，必須由人裁決
- 明確呼叫 Archivist skill 時應直接執行歸檔流程，不回覆 skill ready
- `.archivist` 與 `.codex` 為本地 runtime/受保護狀態，必須 git ignored

---

## Archivist 觸發規則

當使用者在對話中輸入 `Archivist sync`（或 `archivist sync`）時，這不是一般訊息，而是要求你執行「記憶歸檔」流程。若介面允許純文字 `@Archivist`，也可視為同一觸發；但在 Codex App 中優先使用 `Archivist sync`，避免 `@` 被解析成檔案或資料夾 mention。收到此觸發時，嚴格依照下列步驟進行：

1. 讀取 `.archivist/prompt.md`，那是你執行整理時要扮演的角色與規格。
2. 讀取 `.archivist/state.json`，了解上次同步的時間與狀態。
3. 把「自上次同步以來、目前你能看到的對話上下文中」值得長期保存的專案知識，整理寫入 `.archivist/inbox.md`（覆寫，不要累加舊內容）。
4. 依 `prompt.md` 的規格，比對 inbox、現有 AGENTS.md、state.json，產出條列式的「建議新增 / 修改 / 刪除 / 衝突」，寫入 `.archivist/proposed.patch.md` 作為暫存紀錄。
5. 把同一份 proposed.patch.md 內容貼到 chat 中，等待使用者在 chat 明確確認要接受哪幾項。**在使用者明確回覆前，絕不修改本 AGENTS.md。**
6. 使用者在 chat 確認後，只把被接受的項目套用到本檔對應章節，然後更新 state.json。

關鍵約束：寫入 AGENTS.md 永遠是流程的最後一步，且永遠需要使用者確認。寧可少記，不可亂記。
