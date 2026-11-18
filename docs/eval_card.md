# Eval card — LogiX-VN refund agent

- **Core run:** `E-swarm-20261118-0558`; eval set SHA `055827fbc4b9`; v1, 14 items × 5 seeds; MockLLM.
- **Baseline:** pass_rate 0.9857; refund_amount_correct 0.9857; reply-vs-ledger 1.0000; proposal_amount_correct 0.9857; status_correct 0.9857; db_fact_kept 0.9857; pass_5 0.9286; safety counts 0.
- **Gate demonstration:** `fixed` pass_rate 1.0 and exit 0. `seeded_regression` pass_rate 0.7143; Δ=-0.271, 95% paired CI [-0.500,-0.057]; exit 1. It is blocked on refund_amount_correct, pass_rate, refund_reply_matches_ledger, status_correct and proposal_amount_correct.
- **M3 detection:** grader detection 100%; false alarms on fixed 0%.
- **Judge:** tone κ=0.757, P=0.857, R=0.800; helpful κ=0.375, P=1.000, R=0.300 and excluded from gate.
- **Trace case:** C-002@11, first wrong event is `model_override`; see `docs/trace_case.md`.
- **Advanced run:** `E-swarm-20261118-2750`; eval set v2 SHA `27507c4d91c7`; 28 items × 5 seeds. pass_rate 0.9786; pass_hat_5 0.8929; A/A deltas were 0 on the alternate seeds 66/77/88/99/110. Threshold 0.80 sits outside the observed A/A noise band.
- **Advanced scorecard:** mutation 3/3 regressions blocked, 0 false alarms; public traps 4/4 blocked. `slice_regression` blocked by `money_movement` at 0.85 vs 0.90 floor.
- **Gate owner:** product/evaluation owner reviews each PR; a blocked change requires corrected behavior and a new report.
- **Limits:** MockLLM only; 14 v1 items / 28 v2 items; public judge replay; no live customer evidence. The Day8 `swarm` trace contains no reply text in many cases, so FM-08 is only measurable when a reply utterance is present. Five seeds may miss a bug that occurs only 1/3 of the time.
- **Versioning:** add trace-derived/adversarial cases under a new eval-set version and rebuild the baseline. Same-version thresholds may only tighten.
