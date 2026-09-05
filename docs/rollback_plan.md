# Production Business Rule Rollback Plan

## 1. Objective
To guarantee business continuity by providing an instant, zero-downtime, and audited mechanism to revert business rule deployments in the event of unexpected downstream anomalies.

---

## 2. Rollback Protocol & Progression

```
[BR-1.0 Active (Threshold: 100)]
               |
               v (Deploy CR-001)
[BR-2.0 Active (Threshold: 200)]
               |
               v (Anomalous downstream latency detected)
[Initiate Rollback Action: POST /api/changes/{id}/rollback]
               |
               v
[Restored BR-1.0 Active (Threshold: 100)]
```

---

## 3. Operational Anti-Silent Rollback Guarantees

Silent rollbacks (unrecorded state reversions) pose catastrophic compliance and debugging risks. The rollback engine enforces the following non-negotiable guarantees:

1. **Mandatory Justification**: Rollback initiation requires an explicit `reason` string and `initiated_by` actor identifier.
2. **Immutable Audit Entries**:
   - `ROLLBACK_STARTED`: Logs originating and target rule versions with initiator identity.
   - `ROLLBACK_COMPLETED`: Records new active threshold and confirms database state synchronization.
3. **Change Request State Mutation**: The change request record is permanently marked as `ROLLED_BACK` with timestamp and post-mortem notes.
4. **Zero Downtime**: The rule engine updates in-memory evaluation instantly without terminating or rebooting the FastAPI process or supplier adapter connections.

---

## 4. Verification & Testing

Rollback functionality is formally verified in automated test suite `tests/test_rollback.py`:
- In step 5, order quantity 150 evaluates to `NORMAL` under `BR-2.0` (150 < 200).
- Rollback is executed via API.
- In step 7, order quantity 150 immediately evaluates to `PRIORITY_HIGH` under restored `BR-1.0` (150 &ge; 100).
- Audit trail presence of `ROLLBACK_COMPLETED` is verified.
