import json

from scripts.rl.judge_client import judge_completion


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b'{"choices":[{"message":{"content":"{\\"score\\":0.75}"}}]}'


def test_judge_sends_only_question_and_candidate_with_bounded_non_thinking_output(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(request.data)

    monkeypatch.setattr("scripts.rl.judge_client.urllib.request.urlopen", fake_urlopen)
    result = judge_completion(
        "http://judge",
        question="问题正文",
        candidate="rollout答案",
        model="deepseek-v4",
        timeout=12,
        max_tokens=64,
    )

    assert result == '{"score":0.75}'
    payload = captured["payload"]
    prompt = payload["messages"][0]["content"]
    assert "问题正文" in prompt
    assert "rollout答案" in prompt
    assert "参考答案" not in prompt
    assert "标准主张" not in prompt
    assert payload["model"] == "deepseek-v4"
    assert payload["max_tokens"] == 64
    assert payload["chat_template_kwargs"] == {"enable_thinking": False, "thinking": False}
    assert captured["timeout"] == 12
