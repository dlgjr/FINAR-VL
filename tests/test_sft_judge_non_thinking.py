import json

import scripts.sft.pass_at_8_eval as evaluator


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._body).encode("utf-8")


def _row():
    return {
        "task": "open_qa",
        "messages": [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "标准答案"},
        ],
    }


def test_instruct_model_judge_uses_short_output(monkeypatch):
    payloads = []

    def fake_urlopen(request, timeout):
        assert timeout == 300
        payloads.append(json.loads(request.data.decode("utf-8")))
        return _FakeResponse(
            {"choices": [{"message": {"content": "CORRECT"}, "finish_reason": "stop"}]}
        )

    monkeypatch.setattr(evaluator.urllib.request, "urlopen", fake_urlopen)

    assert evaluator._judge_with_server("http://judge", _row(), "标准答案", "标准答案") is True
    assert len(payloads) == 1
    assert payloads[0]["model"] == "qwen30-judge"
    assert "chat_template_kwargs" not in payloads[0]
    assert payloads[0]["structured_outputs"] == {"choice": ["CORRECT", "INCORRECT"]}
    assert payloads[0]["max_tokens"] == 64


def test_model_judge_retry_stays_short(monkeypatch):
    payloads = []

    def fake_urlopen(request, timeout):
        assert timeout == 300
        payloads.append(json.loads(request.data.decode("utf-8")))
        if len(payloads) == 1:
            return _FakeResponse(
                {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}
            )
        return _FakeResponse(
            {"choices": [{"message": {"content": "INCORRECT"}, "finish_reason": "stop"}]}
        )

    monkeypatch.setattr(evaluator.urllib.request, "urlopen", fake_urlopen)

    assert evaluator._judge_with_server("http://judge", _row(), "标准答案", "错误答案") is False
    assert [payload["max_tokens"] for payload in payloads] == [64, 128]
    assert all("chat_template_kwargs" not in payload for payload in payloads)
    assert all(
        payload["structured_outputs"] == {"choice": ["CORRECT", "INCORRECT"]}
        for payload in payloads
    )
