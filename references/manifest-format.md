# 交付清单格式

交付清单使用 JSON，路径相对 `--workspace`。它可以放在临时目录，不要求提交到项目。

## 示例

```json
{
  "schema_version": 1,
  "mode": "HARDEN",
  "status": "PILOT_PACKAGE_READY",
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
    {"kind": "test_plan", "path": "docs/api/test-plan.md"},
    {"kind": "operations_runbook", "path": "docs/api/operations.md"},
    {"kind": "changelog", "path": "docs/api/changelog.md"}
  ],
  "gates": [
    {
      "id": "FIT-01",
      "status": "pass",
      "evidence": [
        {"path": "docs/api/product-scope.md", "detail": "适配结论和目标客户"}
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
- `assessment.target_audience`：外部客户、外部合作伙伴、两者、仅内部、一次性对接方或未知；
- `assessment.business_capability_maturity`：`stable`、`controlled_pilot`、`volatile` 或 `unknown`；
- `tenant_boundary`、`data_action_authority`、`operational_owner` 必须分别达到 `defined`、`confirmed`、`defined`，才能声明试点或 GA 交付就绪；
- `features`：决定条件门禁是否必需；
- `deliverables`：文件可以按项目结构拆分或合并，同一文件可承担多个 kind；
- `gates[].evidence`：每项包含可定位文件和具体说明；
- `gates[].reason`：`fail` 或 `not_applicable` 时必填。

`ASSESSMENT_COMPLETE` 只校验评估内容，不要求交付文件和全部门禁。`PILOT_PACKAGE_READY` 与 `GA_PACKAGE_READY` 必须为 `PRODUCTIZE`，并满足相应交付物与门禁。`EVIDENCE_BLOCKED` 会返回非零状态，防止流水线误判完成。
