# 客户 API 产品化交付

`customer-api-productization` 是一套面向现有软件项目的 Codex Skill。它先判断一项业务能力是否适合开放给外部客户或合作伙伴，再根据真实代码、契约、测试和运行证据，建立或审查可持续维护的 API 产品交付包。

它处理的是接口实现之外的产品化问题：

- 这项能力是否值得、也是否允许对外开放；
- 客户能调用什么，不能调用什么；
- 身份、租户、数据和真实业务动作如何隔离；
- 接口、示例、测试、监控、支持和发布规则是否彼此一致；
- 当前结果只适合继续调研、受控试点，还是已经达到规模化开放门槛。

文档写得多，不代表产品已经准备好。事实或证据不足时，这个 Skill 会停在评估或阻塞状态，不会补写一套看似完整但无法验证的材料。

## 适用范围

### 适合

- 已有可运行的业务能力，希望提供给多个外部客户或合作伙伴长期接入；
- 底层业务流程已基本稳定，至少能支持范围受控的试点；
- 需要建立稳定契约、客户身份、租户隔离、沙箱、版本兼容和支持机制；
- 已经有客户 API，但准备新增能力、扩大试点或正式开放；
- 发布前需要核对产品范围、运行实现、机器契约、测试证据和运维准备是否一致。

### 不适合

- 只新增内部微服务接口；
- 一次性数据交换或短期项目对接；
- 只想生成 OpenAPI、接口文档、Mock 或 SDK；
- 业务状态、收费规则或责任主体仍在频繁变化；
- 无法定义客户身份、租户边界或数据与动作权限；
- 测试请求可能误写生产、触发真实收费或调用真实上游；
- 团队无权开放相关数据或真实业务动作。

这套方法主要面向受控的 B2B 客户或合作伙伴 API。匿名注册、自助创建应用、应用市场等公共开发者平台可以复用其中的 API 核心门禁，但仍需单独建设注册审核、滥用治理、法律条款、开发者门户、生态运营和规模化支持。

## 运行条件

- Codex 能读取待评估项目及其项目规则、代码、契约、测试和文档；
- 实施模式需要对目标项目有相应的文件修改和测试权限；
- Skill 本身不限定语言、框架、协议、单仓或多仓结构；
- 运行交付清单校验器需要 Python 3.10 或更高版本，只使用 Python 标准库；
- 契约解析、运行测试、安全审查和性能测试仍使用目标项目自己的工具链。

没有 Python 也可以完成评估和建设，但无法运行仓库附带的确定性交付清单校验器。

## 安装

### 方式一：让 Codex 安装

在 Codex 中输入：

```text
使用 $skill-installer 从 https://github.com/AlexGitHub0909/customer-api-productization 安装这个 Skill。
```

私有仓库需要当前环境已经具备对应的 GitHub 访问权限。安装完成后，在新一轮对话中使用该 Skill；如果列表没有刷新，重启 Codex。

### 方式二：安装为个人 Skill

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/AlexGitHub0909/customer-api-productization.git \
  "$HOME/.agents/skills/customer-api-productization"
```

个人 Skill 可用于本机上的不同项目。

### 方式三：只在一个项目中使用

在目标仓库根目录执行：

```bash
mkdir -p .agents/skills
git clone https://github.com/AlexGitHub0909/customer-api-productization.git \
  .agents/skills/customer-api-productization
```

项目级安装适合希望团队和仓库版本一起维护 Skill 的场景。是否提交该目录，由项目自己的依赖和仓库管理规则决定。

### 确认是否可用

在 Codex CLI 或 IDE 扩展中执行 `/skills`，或者输入 `$` 查看可用 Skill。列表中应出现 `customer-api-productization`。Codex 支持显式调用，也可能在任务与描述匹配时自动选择它。

Codex 当前的 Skill 发现位置和调用方式以[官方说明](https://developers.openai.com/docs/build-skills)为准。

## 十分钟快速开始

先评估，再决定是否修改项目。

### 1. 在目标项目中启动 Codex

确保当前工作目录是项目根目录，或能覆盖本次需要审查的多个仓库。不要先假设代码一定在 `src/`、`backend/` 或 `docs/`。

### 2. 先做适配评估

```text
使用 $customer-api-productization，以 ASSESS 模式评估当前项目的“订单查询”能力是否适合开放给外部客户。

只读分析，不修改文件。请从项目规则、当前代码、机器契约、测试和运行文档中取证，并明确输出：
1. PRODUCTIZE、DISCOVERY_ONLY 或 NOT_SUITABLE；
2. 已确认事实、未知项和硬阻塞；
3. 若可继续，进入下一阶段所需的最小范围和验证动作。
```

### 3. 根据结论决定下一步

| 结论 | 含义 | 下一步 |
|---|---|---|
| `PRODUCTIZE` | 已具备进入产品化建设的基础 | 选择 `BASELINE`、`EXPAND` 或 `HARDEN` |
| `DISCOVERY_ONLY` | 方向可能成立，但关键事实或授权不足 | 先完成给出的验证任务，不声明试点就绪 |
| `NOT_SUITABLE` | 当前目标不应按客户 API 产品建设 | 采用内部接口、适配器、导入导出或托管操作等替代方案 |

### 4. 建立第一套交付基线

只有评估结论为 `PRODUCTIZE`，并且你确实希望 Codex 修改项目时，再提出实施请求：

```text
使用 $customer-api-productization，以 BASELINE 模式为当前项目建立客户 API 产品化基线。

范围只包括“订单查询”和“订单状态事件”。沿用项目现有目录和事实源，不新建平行文档体系。请补齐机器契约、身份与租户边界、沙箱规则、接入指南、测试矩阵、当前验证报告、运维与发布手册，并生成临时交付清单。不要部署、开通生产或通知客户。
```

### 5. 验收结果

至少核对：

- 最终状态是否与证据一致；
- 产品范围、机器契约、运行实现和示例是否互相匹配；
- “已测试”是否有当前版本的新鲜执行记录；
- 未实现能力是否被明确标记，而不是写成已完成；
- 部署、生产开通、迁移和客户通知是否仍保持未执行状态；
- 交付清单校验器是否按预期返回。

## 四种工作模式

| 模式 | 什么时候使用 | 主要结果 | 不会自动做什么 |
|---|---|---|---|
| `ASSESS` | 还不确定项目或能力是否适合开放 | 适配结论、证据、阻塞项、下一步 | 修改代码或制作完整交付包 |
| `BASELINE` | 有稳定业务能力，但没有可靠的客户 API 基线 | 第一套可审查的产品、契约、安全、测试和运维交付 | 自动部署或开通客户 |
| `EXPAND` | 已有客户 API，需要增加字段、动作、事件或新版本 | 变更影响分析、兼容策略、实现与回归证据 | 默认把破坏性变更塞进原版本 |
| `HARDEN` | 准备试点、GA 或重要版本发布 | 缺口审查、风险修复、门禁证据和最终状态 | 用旧测试或文档存在代替当前验证 |

未指定模式时，Skill 会根据项目现状选择：已有客户 API 通常使用 `HARDEN`；只有业务实现时使用 `BASELINE`；明确新增能力时使用 `EXPAND`。不确定时先用 `ASSESS`。

## 常用请求示例

### 只判断是否值得做

```text
使用 $customer-api-productization，以 ASSESS 模式评估当前仓库是否适合把库存查询能力开放给长期合作伙伴。保持只读，列出结论、依据、未知项和最短解阻路径。
```

### 扩展已有 API

```text
使用 $customer-api-productization，以 EXPAND 模式为现有客户 API 增加批量查询能力。先核对当前版本兼容规则、配额和租户边界，再修改契约、实现、示例、测试、监控和变更记录。不要部署或开通生产。
```

### 发布前加固

```text
使用 $customer-api-productization，以 HARDEN 模式审查 customer-api/v2 的受控试点准备度。修复授权范围内的缺口，重新运行受影响检查，生成交付清单，并明确最终是 PILOT_PACKAGE_READY 还是 EVIDENCE_BLOCKED。
```

### 只审查，不修复

```text
使用 $customer-api-productization 审查当前客户 API 的 GA 准备度。只读，不修改文件。请按门禁列出 pass、fail 和 not_applicable，说明每项证据及其时间，并给出按优先级排序的整改建议。
```

## Skill 如何工作

完整建设按以下阶段推进，前一阶段没有通过，不会把后一阶段写成完成：

1. `FIT`：确认接入对象、复用价值、能力成熟度、授权边界、环境和责任人；
2. `DISCOVERY`：从外部入口追到业务编排、数据、异步流程、外部依赖、测试和现有文档；
3. `PRODUCT_BOUNDARY`：定义目标客户、用例、开放能力、非目标、数据与动作边界；
4. `CONTRACT`：建立机器可读契约及错误、幂等、限流、版本和异步规则；
5. `ACCESS_AND_ENVIRONMENTS`：闭合凭证、授权、租户、审计、沙箱和生产隔离；
6. `DEVELOPER_EXPERIENCE`：提供可执行的接入指南、示例、错误处理和上线清单；
7. `VERIFICATION`：验证契约一致性、权限、隔离、异常、重试和敏感信息边界；
8. `OPERATIONS_AND_RELEASE`：补齐监控、告警、支持、容量、回滚、版本和废弃治理；
9. `RECONCILE`：核对产品、契约、实现、示例、测试、运维和发布记录，运行确定性校验。

目录和技术栈不会改变这些质量门槛。Skill 会先识别项目真实结构，再沿用项目现有文件组织，不强制创建固定的 `docs/api/` 或使用 OpenAPI。

## 交付内容

完整产品化通常覆盖以下九类核心交付物；文件可以按项目习惯拆分或合并：

| 类型 | 要回答的问题 |
|---|---|
| 产品范围 | 谁接入、解决什么、开放什么、不开放什么 |
| 机器契约 | 客户实际可以调用的协议、字段、错误和版本是什么 |
| 接入指南 | 客户如何从凭证开始完成第一条业务闭环 |
| 安全模型 | 身份、scope、租户、敏感字段和高风险动作如何控制 |
| 测试计划 | 哪些正常、异常、边界、安全和隔离风险必须验证 |
| 验证报告 | 当前版本实际运行了什么，结果如何，何时运行 |
| 运维手册 | 如何监控、告警、支持、停用、回滚和处置事故 |
| 变更记录 | 客户可见行为发生了什么变化，如何迁移 |
| 追溯关系 | 产品规则如何对应契约、实现、测试和文档 |

Webhook、批量、异步、受保护文件和正式 SDK 是条件交付物：产品包含时必须通过对应门禁，不包含时要说明业务原因。SDK 不是默认交付物。

## 完成状态

| 状态 | 可以据此说明什么 | 不能据此说明什么 |
|---|---|---|
| `ASSESSMENT_COMPLETE` | 适配评估已经完成 | 已具备试点条件 |
| `PILOT_PACKAGE_READY` | 受控客户试点的交付包和证据达到门槛 | 已部署、已审批或已开通生产 |
| `GA_PACKAGE_READY` | 规模化开放所需的兼容、支持、试点和回滚门禁已通过 | 公共开发者平台整体已经完成 |
| `EVIDENCE_BLOCKED` | 关键事实、权限或验证仍缺失，并已给出解阻路径 | 工作已经完成 |

典型评估结果会把事实和下一步分开：

```text
模式：ASSESS
适配结论：DISCOVERY_ONLY

已确认：存在稳定的订单查询能力；两个外部客户有重复接入需求。
关键缺口：没有可验证的跨租户负向测试，生产数据动作授权仍未确认。
下一步：先确认数据开放责任人，并在隔离环境执行客户 A 访问客户 B 订单的负向用例。

最终状态：ASSESSMENT_COMPLETE
```

典型阻塞结果必须说明影响和最短解阻动作：

```text
最终状态：EVIDENCE_BLOCKED
问题：无法取得当前版本的沙箱隔离测试结果。
影响：不能证明联调请求不会写入生产或触发真实业务动作。
解阻：由平台负责人提供隔离环境，重新执行沙箱副作用和跨租户测试后复审 ENV-01、TENANT-01。
```

## 校验交付清单

交付清单把最终状态、范围、源版本、交付物和门禁证据放在一个临时 JSON 文件中。格式见 [`references/manifest-format.md`](references/manifest-format.md)。它不是新的产品事实源，可以在验收后删除。

### 先运行仓库示例

评估完成示例应返回退出码 `0`：

```bash
python3 scripts/validate_productization.py \
  examples/assessment-manifest.json \
  --workspace .
```

证据阻塞示例应返回退出码 `2`：

```bash
python3 scripts/validate_productization.py \
  examples/blocked-manifest.json \
  --workspace .
```

### 校验真实项目

```bash
python3 /path/to/customer-api-productization/scripts/validate_productization.py \
  /path/to/productization-manifest.json \
  --workspace /path/to/project
```

需要给流水线读取时增加 `--json`：

```bash
python3 /path/to/customer-api-productization/scripts/validate_productization.py \
  /path/to/productization-manifest.json \
  --workspace /path/to/project \
  --json
```

退出码：

- `0`：清单结构有效，且状态不是阻塞；
- `1`：清单字段、文件引用、证据类型或门禁不符合要求；
- `2`：清单结构有效，但最终状态是 `EVIDENCE_BLOCKED`。

校验器会阻止证据路径逃出 `--workspace`，并检查就绪状态所需的交付物、门禁、证据类型和时间范围。它不会判断文档内容是否正确，也不能代替目标项目自己的契约解析、运行测试、安全审查、性能测试或人工产品判断。

## 权限和生产边界

- 评估、审查和报告请求默认保持只读；
- 只有用户明确要求建设、补齐或修复时，才修改目标项目；
- 修改权限不等于部署权限；
- 交付包就绪不等于已经部署、通过审批或开通客户；
- 部署、数据迁移、生产凭证签发、客户开通和客户通知需要分别授权；
- 无法确认数据、合规、商业或上游授权时，必须阻塞或缩小范围；
- 外部写入结果未知时，不能自动重复不可逆请求。

## 仓库结构

```text
customer-api-productization/
├── SKILL.md                              # Codex 执行入口和阶段门禁
├── agents/openai.yaml                    # 展示名称、简介和默认提示词
├── references/
│   ├── applicability.md                  # 适配性、硬阻塞和试点/GA 边界
│   ├── evidence-workflow.md              # 项目结构发现和证据链
│   ├── delivery-contract.md              # 产品化交付要求
│   ├── integration-safety.md             # 幂等、异步、沙箱、事件、文件和凭证安全
│   ├── quality-gates.md                  # 试点、条件和 GA 门禁
│   └── manifest-format.md                # 交付清单字段和证据格式
├── scripts/validate_productization.py    # 确定性交付清单校验器
├── examples/                             # 可直接运行的评估与阻塞清单
└── tests/test_validate_productization.py # 校验器回归测试
```

`SKILL.md` 只保存共同规则和资源路由。Codex 会根据当前任务读取需要的参考文件，不必在每次评估时加载全部材料。

## 常见问题

### Skill 没有出现在列表中

确认安装目录中存在 `customer-api-productization/SKILL.md`，检查 `SKILL.md` 的文件名大小写，然后重启 Codex。项目级 Skill 必须位于当前工作目录到仓库根目录之间的 `.agents/skills/` 下。

### Skill 自动选择了错误模式

在请求中明确写出 `ASSESS`、`BASELINE`、`EXPAND` 或 `HARDEN`，同时说明是否允许修改文件，以及本次能力范围。

### 项目目录和示例完全不同

不需要迁移目录。让 Skill 先识别仓库、运行单元、入口、契约、数据、测试和运维材料，再沿用项目现有结构。`docs/api/` 只是清单格式中的示例路径。

### 校验器提示 `file does not exist`

`deliverables[].path` 和 `gates[].evidence[].path` 默认相对 `--workspace`。把 `--workspace` 指向所有本次交付物和证据的共同根目录，并确保引用的是文件而不是目录。

### 校验器提示 `path escapes workspace`

清单引用了工作区之外的文件。选择合理的共同工作区，或把本次需要保留的证据放入项目允许的位置；不要通过 `../` 绕过边界。

### 校验器通过，是否代表可以上线

不代表。它只验证清单结构、文件引用和声明的门禁。是否能够上线还取决于目标项目的实际测试、安全审批、发布流程以及明确的部署和生产开通授权。

### 为什么返回 `EVIDENCE_BLOCKED`

这不是校验器故障。它表示清单结构可以成立，但关键事实、授权或执行证据不足。按照 `blockers` 中的 `issue`、`impact` 和 `next_step` 完成解阻后，再重新审查。

## 更新与维护

手动安装的个人 Skill 可以这样更新：

```bash
git -C "$HOME/.agents/skills/customer-api-productization" pull --ff-only
```

仓库维护者提交前运行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_productization.py \
  examples/assessment-manifest.json \
  --workspace .
```

Skill 结构校验还应使用当前 Codex `skill-creator` 附带的 `quick_validate.py`。Git 提交和标签是版本事实；如果行为、门禁或清单格式发生变化，应在同一次变更中更新 `SKILL.md`、相关参考文件、测试和 README。
