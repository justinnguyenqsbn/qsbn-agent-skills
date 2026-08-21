---
name: qsbn-sync-to-ado
description: Sync a feature's epic and stories to Azure DevOps specifically. Thin alias over qsbn-sync-to-tracker with the target fixed to azure-devops.
disable-model-invocation: true
---

# qsbn Sync to ADO

Invoke the `qsbn-sync-to-tracker` skill now, with `$ARGUMENTS` as the
feature identifier and `--target azure-devops` fixed, regardless of
whatever `tracker` is set in `.qsbn/config.toml`.

This skill holds no logic of its own — see `qsbn-sync-to-tracker` for the
actual create/update/tagging behavior.
