# Hybrid documentation

Hybrid is the only frontend. Frontend retirement and complete product acceptance
are separate: Classic has been removed, while the remaining verification gates
are recorded explicitly below. Detector/AI implementation and the 24-hour
observation are not part of the current completed work.

| Purpose | Current source |
| --- | --- |
| Installed release, backup and rollback | [Deployment](../HYBRID_DEPLOYMENT.md) |
| Passed checks and outstanding gates | [Acceptance status](../HYBRID_ACCEPTANCE_STATUS.md) |
| Test procedure and evidence rules | [Acceptance workflow](HYBRID_ACCEPTANCE_WORKFLOW.md) |
| Per-route evidence and its limits | [Control register](hybrid-acceptance-route-register.md) |
| Automated regression commands | [Regression](../testing/HYBRID_REGRESSION.md) |
| Isolated browser development | [UI development](local-ui-dev.md) |
| Old navigation URL compatibility | [Redirect map](modern-admin-classic-navigation-inventory.md) |
| Capture cadence and exposure policy | [Capture](../HYBRID_CAPTURE_CADENCE.md) |
| YouTube operations | [YouTube](../HYBRID_YOUTUBE_OPERATIONS.md) |

## Historical design documents

Early Modern Admin V1, information architecture, integration proposal and June
QA audit were removed from current documentation: they instructed developers to
preserve Classic fallback, use its shell and accept intentional placeholders.
They are historical design records, not current operating instructions.
Recover them at commit `e5514ce6` if historical context is needed, for example:

```sh
git show e5514ce6:docs/modern-admin-v1.md
```

Other dated audits and porting reports remain historical unless a current
runbook explicitly cites a still-applicable contract. Their percentages and
past test outcomes do not certify today's product. Follow the current status
and installed-source evidence rather than restarting old migration plans.
