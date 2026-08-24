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


def test_judge_sends_question_candidate_and_interleaved_images_without_reference(monkeypatch, tmp_path):
    captured = {}
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    monkeypatch.setenv("ROOT_IMAGE_DIR", str(tmp_path))

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(request.data)

    monkeypatch.setattr("scripts.rl.judge_client.urllib.request.urlopen", fake_urlopen)
    result = judge_completion(
        "http://judge",
        question="图一：<image>图二：<image>问题正文",
        candidate="rollout答案",
        images=["first.png", "second.png"],
        model="qwen235-judge",
        timeout=12,
        max_tokens=64,
    )

    assert result == '{"score":0.75}'
    payload = captured["payload"]
    content = payload["messages"][0]["content"]
    prompt = "".join(part.get("text", "") for part in content)
    image_urls = [part["image_url"]["url"] for part in content if part["type"] == "image_url"]
    assert "问题正文" in prompt
    assert "rollout答案" in prompt
    assert "参考答案" not in prompt
    assert "标准主张" not in prompt
    assert image_urls == [first.resolve().as_uri(), second.resolve().as_uri()]
    assert [part["type"] for part in content] == ["text", "text", "image_url", "text", "image_url", "text", "text"]
    assert payload["model"] == "qwen235-judge"
    assert payload["max_tokens"] == 64
    assert payload["chat_template_kwargs"] == {"enable_thinking": False, "thinking": False}
    assert captured["timeout"] == 12
