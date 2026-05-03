# Conversational Game Systems 从当前到 MVP 计划书（网页优先）

## 1. 文档目的

本计划书用于把当前仓库能力转化为一个可交付、可验证、可迭代的 MVP（最小可行产品）执行路径。  
MVP 明确采用**网页形态**（浏览器可用），不依赖独立图形客户端，不要求 2D 战术画面。

该文档将作为后续执行对照基线：每个阶段都包含目标、任务、产出、验收标准与风险控制。

---

## 2. 当前项目基线（已具备能力）

基于现有代码与文档，当前基础可概括为三层：

1. **内容与规范层（已具备）**
   - Story Pack 规范：`documents/story-pack-v1-spec.md`
   - 机器校验 Schema：`documents/story-pack-v1.schema.json`
   - 最小样例包：`documents/story-pack-v1.minimal.json`

2. **运行时与校验层（已具备）**
   - 故事包加载与校验入口：`runtime/story_pack.py`
   - 命令行校验：`scripts/validate-story-pack.py`
   - 触发事件筛选、遭遇进入判断等运行时能力（已在测试覆盖范围内）

3. **规则检索层（已具备）**
   - 文本分块 + SQLite FTS5：`rules_index/chunking.py`、`rules_index/storage.py`
   - 实体导入与查找：`rules_index/entities.py`
   - 查询路由：`rules_index/router.py`
   - 建库/导入/评估脚本：`scripts/build-rules-index.py`、`scripts/import-5e-snapshot.py`、`scripts/eval-retrieval-routing.py`

4. **网页展示层（部分具备）**
   - 现有 `pages/` 为静态产品页与文档展示页
   - 尚未形成“可玩会话”网页闭环（缺会话 API 与交互页面）

---

## 3. MVP 定义（必须统一）

### 3.1 MVP 目标

交付一个“可以在网页中完成一次文本冒险体验”的最小产品闭环：

- 用户在网页输入行动或问题
- 系统基于 Story Pack 状态与规则检索给出 AI 叙事回应
- 发生事件触发与基础状态变化
- 可完成一段可验证的短流程（例如“进入地点 -> 对话/选择 -> 触发遭遇文本描述 -> 结算状态”）

### 3.2 MVP 范围（In Scope）

- 网页文本交互（单页即可）
- 后端最小 API（会话、输入、返回）
- Story Pack 加载/校验与运行时事件筛选
- 基础规则检索接入（实体优先 + 规则优先路由）
- 来源/版本可追溯（遵循 `documents/rules-data-sources.md`）
- 最小可部署形态（本地与一套线上环境）

### 3.3 MVP 非范围（Out of Scope）

- 语音输入输出
- 2D 地图与战斗可视化
- 复杂多人同步
- 向量嵌入与 reranker（保留为后续优化）
- 大型运营后台

---

## 4. 总体架构（MVP 版本）

采用“静态网页 + 轻量后端 API + 本地/部署数据库文件”的简单架构：

1. **前端（Web）**
   - 新增一个 MVP 页面（建议 `pages/mvp.html`）
   - 仅实现聊天区、输入框、状态摘要区
   - 不引入重前端框架，优先静态页面 + 轻量 JS

2. **后端（Python API）**
   - 新增最小 Web 服务（建议目录：`app/`）
   - API 提供：
     - `POST /api/session`：创建会话（装载默认故事包）
     - `POST /api/turn`：提交用户输入并返回系统回应、状态变化摘要、可选选项
     - `GET /api/session/{id}`：读取当前状态（调试与断点恢复）
   - 会话存储采用可切换策略（同一 API 契约）：
     - `memory`：本地开发默认
     - `sqlite`：演示/线上默认，支持重启后恢复会话

3. **核心逻辑编排**
   - 复用 `runtime/story_pack.py` 做故事包验证与事件筛选
   - 接入 `rules_index` 查询路由作为辅助知识层
   - 把“模型提示词 + 检索证据 + 状态摘要”组合为一次响应生成输入

4. **可观测性**
   - 记录最小运行日志（会话 ID、回合、路由模式、命中来源）
   - 错误返回统一格式，便于网页提示

### 4.1 API 契约冻结（阶段 1 完成时必须定稿）

为避免前后端反复改接口，阶段 1 结束前冻结以下字段（后续仅允许向后兼容扩展）。

1. `POST /api/session`

- Request:
  - `story_pack_id` (string, optional, default: `story-pack-v1.minimal`)
  - `storage_mode` (string, optional, enum: `memory|sqlite`)
- Response:
  - `session_id` (string)
  - `story_pack_id` (string)
  - `created_at` (ISO8601 string)
  - `state_summary` (object)

1. `POST /api/turn`

- Request:
  - `session_id` (string, required)
  - `user_input` (string, required, 1..2000 chars)
- Response:
  - `session_id` (string)
  - `turn_index` (int)
  - `assistant_text` (string)
  - `state_delta` (object)
  - `state_summary` (object)
  - `options` (array, optional)
  - `metadata` (object):
    - `retrieval_mode` (`entity_first|rules_first|none`)
    - `sources` (array of source attribution entries)
    - `source_system` (string, for version honesty)

1. `GET /api/session/{id}`

- Response:
  - `session_id` (string)
  - `story_pack_id` (string)
  - `turn_index` (int)
  - `state_summary` (object)
  - `last_updated_at` (ISO8601 string)

1. 统一错误结构（全部接口）

- Response:
  - `error` (object):
    - `code` (string, e.g. `SESSION_NOT_FOUND`, `INVALID_INPUT`)
    - `message` (string)
    - `details` (object, optional)

---

## 5. 从现在到 MVP 的阶段执行计划

## 阶段 0：冻结范围与验收标准（0.5 天）

### 阶段 0 目标

避免范围膨胀，锁定 MVP 交付边界。

### 阶段 0 任务

- 固化本文档的 In Scope/Out of Scope
- 定义 Demo 流程（建议 5~8 回合）
- 明确“可上线最小条件”

### 阶段 0 产出

- 本计划书定稿
- Demo 脚本（可写入 `documents/mvp-demo-script.md`）

### 阶段 0 验收标准

- 团队对 MVP 范围无歧义
- 每个功能项可映射到后续阶段任务

---

## 阶段 1：后端最小可用 API 骨架（1~2 天）

### 阶段 1 目标

让网页能真实调用后端完成会话闭环。

### 阶段 1 任务

- 新建 `app/` 服务入口与路由
- 实现会话存储抽象（统一接口）：
  - `MemorySessionStore`（开发默认）
  - `SQLiteSessionStore`（演示/线上默认）
- 接入 `load_story_pack`，会话创建时载入默认包
- 实现 `POST /api/session` 与 `GET /api/session/{id}`（按 4.1 契约）
- 增加基础 API 测试（`tests/test_api_session.py`）
- 同步更新 `AGENTS.md`（新增 `app/` 目录映射）与 `README.md`（最小启动说明）

### 阶段 1 产出

- 可运行的本地 API 服务
- 会话创建/读取流程可测试

### 阶段 1 验收标准

- 单元测试通过
- 使用 curl/脚本可创建并读取会话
- 切换到 `sqlite` 存储后，服务重启仍可读取已有会话
- API 字段与错误结构与 4.1 一致

---

## 阶段 2：单回合编排（输入 -> 状态 -> 输出）（2~3 天）

### 阶段 2 目标

打通游戏核心回合，支持最小叙事响应。

### 阶段 2 任务

- 实现 `POST /api/turn`（按 4.1 契约）
- 回合逻辑最小链路：

  1) 解析输入
  2) 触发 Story Pack 事件筛选（`find_triggered_events`）
  3) 应用基础 outcome（至少支持 `set_flag`、`set_variable`、`narrate`、`start_encounter` 文本化）
  4) 构造响应文本与状态摘要

- 增加回合测试（`tests/test_api_turn.py`）

### 阶段 2 产出

- 可持续推进的文本回合引擎（MVP 级）

### 阶段 2 验收标准

- 给定固定输入序列，状态变更可预测
- 关键逻辑测试通过（含非法 session、非法输入）
- `metadata` 字段存在且结构稳定（未接入检索时可返回 `retrieval_mode=none`）

---

## 阶段 3：规则检索接入（1~2 天）

### 阶段 3 目标

让 AI 或系统响应具有可追溯规则依据。

### 阶段 3 任务

- 在 `POST /api/turn` 中接入 `rules_index/router.py`
- 至少实现：

  - `entity_first` 路径一次查询
  - `rules_first` 路径一次查询

- 把检索来源（source_system、标题/实体）附在响应元数据中
- 增加检索链路测试（可用 fixtures）

### 阶段 3 产出

- 回应可带“依据来源”的 metadata

### 阶段 3 验收标准

- 两类查询均可命中并返回来源
- 不命中时有清晰降级策略（例如“未找到明确规则依据”）
- 返回的 `source_system` 与版本标识符合 `documents/rules-data-sources.md`

---

## 阶段 4：网页 MVP 页面（1~2 天）

### 阶段 4 目标

用户在浏览器中可完成一轮到多轮文本游玩。

### 阶段 4 任务

- 新增 `pages/mvp.html`（或 `pages/play.html`）
- 新增轻量脚本（可放 `pages/mvp.js`）：

  - 初始化会话
  - 发送回合输入
  - 渲染对话记录与状态摘要
  - 展示错误与 loading 状态

- 保持视觉风格与 `pages/style.css` 一致

### 阶段 4 产出

- 浏览器可玩的文本版试玩页

### 阶段 4 验收标准

- 打开网页后无需开发者操作即可开始会话
- 完成预设 Demo 流程（5~8 回合）无阻塞错误

---

## 阶段 5：稳定性与发布准备（1~2 天）

### 阶段 5 目标

把“能跑”提升到“可演示、可复现、可交付”。

### 阶段 5 任务

- 增加最小 E2E 脚本（API 层面）
- 补充 README 的 MVP 运行说明（本地启动、依赖、环境变量）
- 补充 `documents/` 下的测试清单与已知限制
- 建立最小 CI/CD 流水线（GitHub Actions）：
  - CI：安装依赖 -> 单元测试 -> API smoke/E2E 脚本
  - CD（最小形态）：`main` 分支通过后触发部署脚本或手动审批部署到单一演示环境
- 执行 release checklist（仓库已有对应 skill）

### 阶段 5 产出

- 一套完整演示与复现说明
- 已知限制透明化文档

### 阶段 5 验收标准

- 新成员按文档可在本地完成 MVP 启动与体验
- 关键测试全部通过
- CI 必须稳定通过；CD 路径可被一次完整演练（含回滚说明）

---

## 6. 建议里程碑与节奏（10~14 天）

- **M1（第 2 天）**：API 会话骨架可用
- **M2（第 5 天）**：单回合编排稳定可测
- **M3（第 7 天）**：检索接入并输出来源
- **M4（第 9 天）**：网页可玩闭环完成
- **M5（第 12~14 天）**：文档、测试、演示打包完成

> 如资源紧张，优先保证 M2 + M4，其他项可降配但不删除“来源透明”和“状态可追踪”。

---

## 7. 验收标准（MVP Done Definition）

满足以下全部条件即视为 MVP 完成：

1. 网页可创建会话并完成多轮文本交互
2. 至少一个 Story Pack 流程可稳定重放
3. 关键状态变化可被显示或查询
4. 回应中可附带规则来源或明确说明未命中
5. 主要测试通过，文档可复现部署/运行
6. 不依赖语音、2D 图形客户端能力
7. 最小 CI/CD 流程可运行，且与本地验证步骤一致

---

## 8. 风险与缓解（执行期）

1. **规范与实现偏离**
   - 缓解：以 `runtime/story_pack.py` + 自动化测试作为执行事实源；变更必须同步 spec/schema

2. **检索命中不稳定**
   - 缓解：先扩 `eval/queries.yaml` 到真实查询集；为低置信度结果提供降级话术

3. **回合逻辑过快复杂化**
   - 缓解：MVP 仅支持有限 outcome 类型；复杂机制先文档化不实现

4. **网页与后端接口反复改动**
   - 缓解：阶段 1 先冻结 API 契约，再进入页面开发

5. **上线演示时环境不一致**
   - 缓解：提供单一启动命令和固定依赖版本，演示前全流程回归

---

## 9. 执行对照清单（每次迭代都打勾）

- [ ] 本轮目标是否属于 MVP In Scope
- [ ] 是否新增/更新对应测试
- [ ] 是否更新运行文档与限制说明
- [ ] 是否验证网页回归流程（创建会话 -> 3 回合交互）
- [ ] 是否检查来源展示与版本标识
- [ ] 是否确认未误提交 `vendor/` 与 `build/` 产物
- [ ] 是否在 `documents/progress-log.md` 记录本轮进展

---

## 10. 下一步建议（立即执行）

建议按以下顺序立刻进入实现（阶段 1 完成即冻结 API 契约）：

1. 建立 `app/` 最小 API 骨架（阶段 1）
2. 实现 `POST /api/turn` 的最小链路（阶段 2）
3. 接入规则检索并输出来源 metadata（阶段 3）
4. 创建 `pages/mvp.html` 并连通 API（阶段 4）
5. 补齐最小 CI/CD 与发布检查（阶段 5）

当 1~4 完成后，项目进入“可试玩产品”状态；当第 5 步完成后，进入“可稳定演示与可交付”状态。
