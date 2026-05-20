# Archivist

Archivist 是一個輕量的 repo-level 記憶歸檔工具。它跑在 Codex 對話流程上，之後也可移植到 Claude Code。它只做一件事：當 `AGENTS.md` 的守門員。

跟 AI 協作開發時，技術選型、coding style、workflow 偏好、專案規則常常是在對話裡拍板，但這些知識不會自動沉澱。Archivist 的做法是：平常照常對話，只有需要整理專案知識時輸入 `Archivist sync`。AI 先判斷哪些內容長期有效、值得保存，直接在 chat 中列出 `[ADD] / [MOD] / [DEL] / [!!]` 建議；你在 chat 裡明確確認後，才把接受的項目寫入 `AGENTS.md`。

Archivist 刻意不做 UI、不做 marketplace、不做多 agent 協作。差異化在三件事：嚴格篩選長期知識、逐項確認的 diff 體驗、主動偵測衝突與膨脹。

## Files

```text
AGENTS.md                         專案知識本體，Codex 每次 session 會讀取
archivist.py                      CLI：初始化、檢查、顯示提案、套用已確認項目
templates/archivist/              安裝到目標 repo 時使用的初始模板
.archivist/                       本 repo 的 runtime 狀態（git ignored）
tests/                            CLI 核心行為測試
```

`templates/archivist/` 是初始化 `.archivist/` 時使用的乾淨模板；`.archivist/` 是每個 repo 的本地 runtime 狀態，不應作為 skill source。

## Codex App Quick Start

Clone and install the Archivist skill:

```bash
git clone <repo-url>
cd Archivist
python scripts/install.py
```

If `python` is not on PATH on Windows, either enable Python's "Add to PATH" option or run with the full Python executable path.

Then restart Codex App or open a new chat, and run:

```text
/Archivist
```

Fallback trigger:

```text
Archivist sync
```

To also initialize a target repo:

```bash
python scripts/install.py --init-repo /path/to/your/repo
```

### Skill Mode

Codex App 原生用法是安裝 skill：

```text
C:\Users\Michael\.codex\skills\archivist
```

本 repo 也保留同一份 source：

```text
skills/archivist/SKILL.md
skills/archivist/references/workflow.md
skills/archivist/scripts/archivist.py
```

安裝後可用自然語意觸發，例如：

```text
Archivist sync
```

skill 會在 chat 中提出 `[ADD] / [MOD] / [DEL] / [!!]` 建議；你在 chat 中確認後，Codex 才能寫入 `AGENTS.md`。

### Repo Install Mode

先把 Archivist 安裝到你要使用的目標 repo：

```bash
python archivist.py install /path/to/your/repo
```

在 Windows / Codex Desktop 裡，如果系統 PATH 沒有 Python，可用 bundled runtime：

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" archivist.py install "C:\path\to\your\repo"
```

安裝會做四件事：

1. 在目標 repo 建立 `.archivist/`。
2. 複製 `prompt.md`、`inbox.md`、`proposed.patch.md`、`state.json`。
3. 確保目標 repo 的 `AGENTS.md` 有 Archivist 固定章節與 `Archivist sync` 觸發規則。
4. 複製 `archivist.py` 到目標 repo，讓該 repo 自己可以套用確認後的提案。

之後在 Codex App 開啟目標 repo，平常正常開發。需要整理專案記憶時，在對話輸入：

```text
Archivist sync
```

不要用 `@Archivist` 當主要觸發詞；Codex App 可能會把 `@` 解析成檔案或資料夾 mention。`@Archivist` 只保留為其他介面可用時的 alias。

Codex 會依 `AGENTS.md` 的觸發規則：

1. 讀取 `.archivist/prompt.md`。
2. 將目前可見上下文中值得長期保存的資訊覆寫到 `.archivist/inbox.md`。
3. 產生 `.archivist/proposed.patch.md` 作為暫存紀錄。
4. 把同一份建議貼在 chat 裡，等待你回覆 `1,3`、`all`、`none` 或修改後的項目。

你在 chat 裡確認要接受哪些項目後，Codex 可以在目標 repo 裡替你執行：

```bash
python archivist.py apply 1,3
python archivist.py apply all
python archivist.py apply 1-4 --dry-run
```

`apply` 是確認後的後台套用步驟，不是使用者確認介面。確認介面永遠是 chat。`apply` 只套用 `proposed.patch.md` 裡被你選到的 `[ADD] / [MOD] / [DEL]`。`[!!]` 衝突項目不會自動套用，即使被選到也只會被跳過，必須由人手動裁決後改成明確的 `[MOD]` 或 `[DEL]`。

## Local Development

初始化工作目錄：

```bash
python archivist.py init
```

檢查必要檔案與 `AGENTS.md` schema：

```bash
python archivist.py check
```

查看已產生的提案：

```bash
python archivist.py show
```

## Proposal Format

chat 中顯示的建議與 `.archivist/proposed.patch.md` 暫存紀錄都使用這幾種一行式提案：

```text
[ADD] <章節> → <精簡內容>
[MOD] <章節> #<編號>: <舊> → <新>
[DEL] <章節> #<編號>: <內容> ← <刪除理由>
[!!]  <章節> #<編號> 與本次衝突：現有「<舊>」 vs inbox「<新>」
```

章節必須是 `AGENTS.md` 的固定 schema：

- `Architecture Decisions`
- `Coding Style`
- `Workflow`
- `Tooling`
- `Project Rules`

## Tests

```bash
python -m unittest discover -s tests
```

在 Codex Desktop 內若系統 PATH 沒有 Python，可使用 bundled runtime，例如：

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests
```
