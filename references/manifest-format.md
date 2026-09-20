# 交付清单格式

交付清单使用 JSON，路径相对 `--workspace`。它可以放在临时目录，不要求提交到项目。

## 示例

```json
{
  "schema_version": 1,
  "mode": "HARDEN",
  "status": "PILOT_PACKAGE_READY",
  "source_revision": "git:4f21c88-dirty",
  "evaluated_at": "2026-09-20T16:30:00+08:00",
  "evidence_cutoff_at": "2026-09-01T00:00:00+08:00",
  "scope": [
    "客户身份与凭证",
    "报价创建与查询",
    "Webhook 投递"
  ],
  "assessment": {
    "fit_decision": "PRODUCTIZE",
    "target_audience": "external_customers",
    "repeatable_integration": true,
    "business_capability_maturity": "controlled_pilot",
    "tenant_boundary": "defined",
    "data_action_authority": "confirmed",
    "operational_owner": "defined",
    "rationale": [
      "已有两个客户需要持续接入同一业务闭环",
      "租户、权限和生产责任已经明确"
    ]
  },
  "features": {
    "webhooks": true,
    "async_operations": true,
    "protected_files": false,
    "batch_operations": false,
    "official_sdk": false
  },
  "deliverables": [
    {"kind": "product_scope", "path": "docs/api/product-scope.md"},
    {"kind": "machine_contract", "path": "docs/api/openapi.yaml"},
    {"kind": "integration_guide", "path": "docs/api/integration-guide.md"},
    {"kind": "security_model", "path": "docs/api/security-model.md"},
    {"kind": "test_plan", "path": "docs/api/test-plan.md"},
    {"kind": "verification_report", "path": "docs/api/verification-report.md"},
    {"kind": "operations_runbook", "path": "docs/api/operations.md"},
    {"kind": "changelog", "path": "docs/api/changelog.md"},
    {"kind": "traceability", "path": "docs/api/traceability.md"}
  ],
  "gates": [
    {
      "id": "FIT-01",
      "status": "pass",
      "evidence": [
        {
          "type": "decision",
          "path": "docs/api/product-scope.md",
          "detail": "适配结论、目标客户和硬阻塞核对"
        }
      ]
    },
    {
      "id": "TEST-01",
      "status": "pass",
      "evidence": [
        {
          "type": "test_run",
          "path": "docs/api/verification-report.md",
          "detail": "当前 revision 的隔离测试、负向测试和回归结果",
          "observed_at": "2026-09-20T16:10:00+08:00"
        }
      ]
    }
  ],
  "notes": [
    "交付包就绪；尚未部署或开通生产"
  ]
}
```

实际清单需要列出对应状态要求的全部门禁。

## 核心字段

- `mode`：`ASSESS`、`BASELINE`、`EXPAND`、`HARDEN`；
- `status`：`ASSESSMENT_COMPLETE`、`PILOT_PACKAGE_READY`、`GA_PACKAGE_READY`、`EVIDENCE_BLOCKED`；
- `assessment.fit_decision`：`PRODUCTIZE`、`DISCOVERY_ONLY`、`NOT_SUITABLE`；
- `assessment.target_audience`：`external_customers`、`external_partners`、`external_customers_and_partners`、`internal_only`、`one_off_counterparty` 或 `unknown`；
- `assessment.business_capability_maturity`：`stable`、`controlled_pilot`、`volatile` 或 `unknown`；
- `assessment.tenant_boundary`：`defined`、`partial`、`missing` 或 `unknown`；
- `assessment.data_action_authority`：`confirmed`、`partial`、`missing` 或 `unknown`；
- `assessment.operational_owner`：`defined`、`partial`、`missing` 或 `unknown`；
- `PRODUCTIZE` 必须同时满足外部受众、可重复接入、`stable` 或 `controlled_pilot`、租户边界 `defined`、数据动作授权 `confirmed`、运营责任 `defined`；
- `source_revision`：Git SHA、发布版本或其它可复现的源版本；有未提交修改时明确附加 dirty 说明；
- `evaluated_at`：带时区的 ISO 8601 审查时间；
- `evidence_cutoff_at`：本次判断接受的最早执行证据时间，由项目按变更风险和发布节奏确定；不得晚于 `evaluated_at`；
- `scope`：本次实际覆盖的能力列表；
- `next_steps`：`ASSESSMENT_COMPLETE` 必须给出从当前结论进入下一阶段或替代方案的具体动作；
- `features`：决定条件门禁是否必需；
- `deliverables`：文件可以按项目结构拆分或合并，同一文件可承担多个 kind；
- `gates[].evidence`：每项包含 `type`、可定位文件和具体说明；执行型证据还必须包含带时区的 `observed_at`；
- `gates[].reason`：`fail` 或 `not_applicable` 时必填。

`ASSESSMENT_COMPLETE` 只校验评估内容，不要求交付文件和全部门禁。`PILOT_PACKAGE_READY` 与 `GA_PACKAGE_READY` 必须为 `PRODUCTIZE`，并满足相应交付物与门禁。`EVIDENCE_BLOCKED` 会返回非零状态，防止流水线误判完成。

## 证据类型

可用类型：

- 决策与静态材料：`decision`、`implementation`、`artifact`、`manual_review`、`approval`；
- 执行和观察结果：`contract_check`、`runtime_check`、`test_run`、`example_run`、`security_review`、`performance_check`、`operations_record`、`pilot_run`。

执行和观察结果必须带 `observed_at`，时间必须落在 `evidence_cutoff_at` 到 `evaluated_at` 之间。校验器会要求契约、运行时、测试、示例、安全、容量、试点和回滚门禁至少包含匹配类型，避免用一份说明文档代替实际验证。

## 阻塞状态

`EVIDENCE_BLOCKED` 必须提供非空 `blockers`：

```json
{
  "blockers": [
    {
      "issue": "生产租户隔离测试环境不可用",
      "impact": "无法确认客户 A 不会读取客户 B 的订单",
      "next_step": "由平台工程提供隔离测试环境并重新执行跨租户负向用例"
    }
  ]
}
```

只写“待确认”不够；每项都要说明问题、影响和最短解阻动作。
