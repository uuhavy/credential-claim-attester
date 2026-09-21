# CredentialClaimAttester

## Deployment

- **CONTRACT_ADDRESS:** `0x7516772B9B955bdf3bCCfC86DBf01edDb20Fa322`
- **NETWORK:** `studionet`
- **Explorer:** [public contract](https://explorer-studio.genlayer.com/address/0x7516772B9B955bdf3bCCfC86DBf01edDb20Fa322)
- **Deployment transaction:** [0xfb4f2784ae7eb7504e4b71baf13c0287dd0cc37d5fba034dd77ab361b89edd21](https://explorer-studio.genlayer.com/tx/0xfb4f2784ae7eb7504e4b71baf13c0287dd0cc37d5fba034dd77ab361b89edd21)
- **Evidence status:** FINALIZED / SUCCESS, verified 2026-09-21 on public studionet RPC (chain ID 61999). `gen_getContractCode` matches the repository source byte-for-byte; `gen_getContractSchema` returns all four methods; real `get_count()` returns `0`. Explorer independently displays the contract and successful finalized deployment. See [verification JSON](deployment-verification.json), [receipt summary](deployment-receipt.json) and [manifest](deployment-studionet.json).
- **Correction:** the previous address `0x8f0Cfbf5B297bD75a665e9c8A42082cAF99ce17D` did not resolve and must not be reused for submission. The same unchanged source was redeployed publicly. The contract has no owner/admin field; the dedicated test deployer does not acquire privileged rights.
- **Local validation:** all **66 tests passed** using a five-validator local glsim. See [VALIDATION.md](VALIDATION.md) for environment and compatibility fixes. This is not a production network result.

### Worked example — illustrative input and expected output

A candidate claims a personal certification but links the general AWS exam page:

```python
submit_claim(
    "I hold the AWS Certified Solutions Architect - Associate certification.",
    "https://aws.amazon.com/certification/certified-solutions-architect-associate/"
)
```

**Expected decision, not executed on studionet:**

```json
{
  "verdict": "UNSUPPORTED",
  "confidence": 25,
  "reason": "The page describes the certification and exam but supplies no individual credential supporting the submitter's claim."
}
```

The [AWS page](https://aws.amazon.com/certification/certified-solutions-architect-associate/) describes an exam, not the candidate's credential. This verdict is an illustrative expectation; the confidence and wording are examples, not measured outputs or guarantees. After successful consensus, `submit_claim` returns a new string ID. `get_attestation(id)` returns the decision plus `attestation_id`, actual sender address, claim and URL. No live ID or transaction hash is fabricated here.

## Mục đích

Primitive GenLayer độc lập đánh giá mức độ bằng chứng web công khai hỗ trợ một claim kỹ năng, kinh nghiệm hoặc chứng chỉ. Mỗi kết quả được lưu bất biến cùng địa chỉ ví gửi giao dịch, claim, URL, verdict, confidence và lý do ngắn. Không có frontend hay oracle trung gian riêng.

## Khả năng tái sử dụng

Input được tham số hóa: bất kỳ người dùng nào cũng có thể gửi claim và URL khác nhau. DAO có thể dùng để vetting thành viên, job board lọc ứng viên, quỹ tài trợ xét cộng tác viên và hệ thống freelancer tổng hợp reputation bằng cách đọc cùng một API. Đây là primitive có state và lịch sử truy vấn được, thay vì một prompt chỉ xử lý một ví dụ cố định.

## Consensus và validator

`submit_claim` lấy claimant từ `gl.message.sender_address`. Trong inner `leader_fn`, contract đọc tối đa 6.000 ký tự bằng `web.render(..., mode="text")` và gọi `exec_prompt(..., response_format="json")`. Prompt coi claim và nội dung trang là dữ liệu không đáng tin cậy, yêu cầu bỏ qua chỉ dẫn nhúng trong bằng chứng.

`gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` gửi kết quả đã chuẩn hóa của leader tới validator. Validator yêu cầu `gl.vm.Return`, parse JSON và tự chạy lại quy trình đọc web/đánh giá bằng LLM của mình. Chỉ đồng ý khi verdict giống nhau và confidence nằm cùng band:

| Band | Confidence |
| --- | --- |
| 0 | 0–34 |
| 1 | 35–79 |
| 2 | 80–100 |

Ví dụ SUPPORTED/85 và SUPPORTED/95 đồng thuận dù reason khác nhau; SUPPORTED/79 và SUPPORTED/80 không đồng thuận. Validator kiểm ý nghĩa phân loại và mức tin cậy, không so chuỗi JSON hay văn phong. Reason được lưu từ leader và **không được kiểm chứng riêng về ngữ nghĩa**. Confidence là điểm đánh giá của mô hình, không phải xác suất đã được hiệu chuẩn.

Verdict được strip/uppercase; confidence nguyên được clamp về 0–100; reason được strip và cắt 400 ký tự. JSON lỗi, thiếu field, verdict lạ, confidence sai kiểu hoặc reason rỗng đều bị từ chối. Validator bắt lỗi và trả `False`; contract không tự tạo attestation thay thế cho lỗi LLM. Retry/appeal tùy cơ chế mạng, không được bảo đảm sẽ thành công.

## State và API

State dùng `TreeMap[str, Attestation]`, `TreeMap[str, DynArray[str]]`, `next_id: bigint`; struct có `@allow_storage` và `@dataclass`. ID bắt đầu từ `"0"`. Không có sửa/xóa attestation.

`__init__` chỉ gán `next_id`. Mảng theo ví được cấp phát bằng `get_or_insert_default`, vì SDK không cho gọi `DynArray()` trực tiếp. Không có `dict`/`list` persist; những object này chỉ dùng tạm để tạo JSON. Địa chỉ được chuẩn hóa qua `Address.as_hex`.

| Public method | Kết quả |
| --- | --- |
| `submit_claim(skill_claim: str, evidence_url: str) -> str` | Write; trả ID mới, lấy ví từ sender |
| `get_attestation(attestation_id: str) -> str` | View; JSON object hoặc `UserError("attestation not found")` |
| `get_claims_by_address(address: str) -> str` | View; JSON array đầy đủ theo thứ tự gửi; chưa có trả `"[]"` |
| `get_count() -> int` | View; tổng số attestation |

JSON trả về gồm `attestation_id` và sáu field của Attestation. ID được thêm ở lớp trả JSON để ứng dụng nhận diện bản ghi, không thêm field vào storage struct.

## Ví dụ sử dụng

Trong Studio, gọi write `submit_claim("AWS Solutions Architect certified", "https://example.com/certificate")`, nhận ID `"0"` cho lần đầu; sau khi giao dịch thành công gọi view `get_attestation("0")`.

Ví dụ fluent API của gltest, với `contract` đã deploy và `account` đã cấu hình:

```python
import json
from gltest.assertions import tx_execution_succeeded

receipt = contract.connect(account).submit_claim(args=[
    "AWS Solutions Architect certified",
    "https://example.com/certificate",
]).transact(value=0)
assert tx_execution_succeeded(receipt)
attestation = json.loads(contract.get_attestation(args=["0"]).call())
```

URL trên chỉ minh họa; khi sử dụng thực tế cần URL bằng chứng thật. `.transact()` trả receipt, không phải trực tiếp ID. Không suy ra ID bằng `get_count()` khi có nhiều người gửi đồng thời; đọc return data giao dịch hoặc lịch sử theo ví.

## Edge cases

| Trường hợp | Xử lý |
| --- | --- |
| URL thiếu prefix http/https | `UserError` trước khi gọi web/LLM |
| Claim rỗng hoặc toàn khoảng trắng | `UserError` trước khi thay đổi state |
| Web lỗi hoặc rỗng | Bắt lỗi render, gửi evidence rỗng tới LLM; prompt yêu cầu UNSUPPORTED với confidence 0–34 |
| PARTIAL / UNSUPPORTED | Lưu giống SUPPORTED nếu đạt consensus |
| LLM JSON lỗi hoặc thiếu field | Không lưu; validator trả False khi parse hoặc tự đánh giá thất bại |
| Nhiều claim cùng ví | Append ID; giữ đúng thứ tự, không ghi đè |
| ID không tồn tại | `UserError("attestation not found")` |
| Ví chưa có claim / địa chỉ không parse được | Trả `"[]"` |

## Chạy test

Yêu cầu Python 3.12+. Từ thư mục này:

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/prepare_windows_tests.py
python scripts/prepare_glsim_tests.py
# Prime the pinned SDK cache before starting glsim:
python -m pytest tests/test_direct.py -v
# In a second terminal using the same venv:
glsim --no-browser --seed credential-claim-attester-tests
# Back in the test terminal:
gltest tests/ -v
# Optional individual suites:
python -m pytest tests/test_logic.py -v
python -m pytest tests/test_direct.py -v
gltest tests/test_credential_claim_attester.py -v
```

Direct tests pin SDK release `v0.2.16` để tránh tải bản latest không phù hợp; lần đầu tải SDK từ GitHub. Chúng chạy Python với SDK storage và mock của gltest, không thay thế kiểm tra trong GenVM thật.

Studio integration tests cần simulator tại `http://127.0.0.1:4000/api`, validator đã cấu hình, và hỗ trợ RPC `sim_installMocks`. Test cài mock trước mỗi write non-deterministic với `params` là dict trực tiếp, rồi xóa mock sau test. Đây là mock toàn simulator: chạy trên instance test riêng và không chạy song song. Nếu RPC báo method not found, cần simulator tương thích; bộ test cố ý báo lỗi thay vì âm thầm gọi LLM thật. Không dùng `--leader-only` để xác nhận consensus.

## Deploy trên Studio

1. Mở [Studio Run & Debug](https://studio.genlayer.com/run-debug).
2. Dùng môi trường test riêng; reset storage trước khi deploy bản mới. Reset sẽ xóa state test cũ.
3. Dán nguyên file `contracts/credential_claim_attester.py`, giữ nguyên ba dòng đầu. Class runtime tên `Contract`; tên sản phẩm là CredentialClaimAttester.
4. Deploy với constructor không có tham số; kiểm tra UI báo `Result: SUCCESS`.
5. Gọi `get_count()` kỳ vọng 0, gửi claim với bằng chứng thật, chờ thành công rồi kiểm tra ba view.

## Giới hạn tích hợp

Gắn bản ghi với sender chứng minh ai gửi claim, **không chứng minh ví sở hữu GitHub/LinkedIn/chứng chỉ được dẫn**. Ứng dụng cần kiểm tra liên kết danh tính riêng trước khi dùng cho cấp quyền. SUPPORTED chỉ là đánh giá sự hỗ trợ của bằng chứng được cung cấp.

Trang có thể thay đổi giữa leader và validator; nội dung sau 6.000 ký tự bị bỏ qua, trang đăng nhập có thể không đọc được. Không lưu snapshot/hash/timestamp bằng chứng nên không tái dựng đầy đủ trang tại thời điểm đánh giá. Prompt có hướng dẫn chống injection nhưng không bảo đảm mô hình miễn nhiễm. Lịch sử theo ví trả toàn bộ array; ví có quá nhiều claim có thể chạm giới hạn tài nguyên. Claim, URL và kết quả là dữ liệu công khai.

## Tài liệu tham chiếu

- [GenVM SDK: storage, Address và run_nondet_unsafe](https://sdk.genlayer.com/v0.2.9/api/genlayer.html)
- [GenLayer Testing Suite](https://docs.genlayer.com/api-references/genlayer-test)

Header version và dependency hash được giữ nguyên theo yêu cầu; trạng thái kiểm tra thực tế xem `VALIDATION.md`.

The preparation scripts only repair the pinned test tooling: Windows open-file cleanup and glsim schema/class discovery behind its calldata proxy. They do not change contract execution, storage, mocks or voting rules. See [REVIEW.md](REVIEW.md) for the primitive review and limitations.

### Reproduce public verification

From this project directory with requirements-dev.txt installed:

```sh
python scripts/verify_public.py
```

This requires no browser login or saved wallet key. It checks chain ID, finalized
deployment, deployed source, schema and a real read. It records current results
in deployment-verification.json. The deployment key is kept only in the local,
gitignored .env.studionet-deployer file; it is not needed to verify or use the
public contract. No mock or leader-only configuration was used for deployment.
