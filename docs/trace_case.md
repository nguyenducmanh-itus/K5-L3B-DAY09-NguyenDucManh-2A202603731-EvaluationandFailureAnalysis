# Trace case: first wrong decision and regression check

## Trial

`seeded_regression C-002@11`, report `E-seeded_regression-20261118-0558` (eval set SHA `055827fbc4b9`). Đối chứng: `fixed C-002@11`, cùng input và seed.

## Kết quả

- **Triệu chứng:** seeded trả `status=resolved`, ghi refund 20.000đ và grader Lab 8 báo `status resolved != denied`; fixed trả `denied`, ledger 0đ và grader PASS.
- **Bước sai đầu tiên:** event 3 của seeded là `model_override` với `delay_days: 5`. Đây là điểm trace đầu tiên dùng ticket claim để ghi đè facts/policy; event 4 sau đó quote 20.000đ và event 6 mới tuyên bố đã hoàn.
- **Đối chứng:** fixed không có event `model_override`; event 3 quote 0 với `no_entitlement`, event 4 reply từ chối hoàn.
- **Failure mode:** FM-03 `ticket_trust`.
- **Regression checks:** `DbFactKept` bắt event override; `TrialPass` bắt kết quả sai; `RefundAmountCorrect` bắt ledger khác nhãn. Các test M3 trong `tests/test_lab9_graders.py` xác nhận grader độc lập trên Trial dựng sẵn.
- **Chưa chứng minh:** một replay MockLLM không đại diện mọi câu ticket hay model thật; 5 seed không bảo đảm thấy lỗi hiếm 1/3 lần.

Chạy lại bằng `python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11` và đối chứng `--shape fixed`.

