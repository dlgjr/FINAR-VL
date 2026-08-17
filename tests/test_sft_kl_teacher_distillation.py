from scripts.sft.kl_retention_plugin import (
    _content_with_images,
    _replace_assistant_with_teacher,
)


def test_multimodal_teacher_content_preserves_image_order():
    parts = _content_with_images(
        "先看<image>再比较<image>。",
        ["file:///tmp/a.png", "file:///tmp/b.png"],
    )
    assert parts == [
        {"type": "text", "text": "先看"},
        {"type": "image_url", "image_url": {"url": "file:///tmp/a.png"}},
        {"type": "text", "text": "再比较"},
        {"type": "image_url", "image_url": {"url": "file:///tmp/b.png"}},
        {"type": "text", "text": "。"},
    ]


def test_teacher_response_replaces_dataset_assistant_answer():
    record = {
        "messages": [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "数据集自带答案"},
        ],
        "task": "generation",
    }
    updated = _replace_assistant_with_teacher(record, "base自己生成的答案")
    assert updated["messages"][-1] == {"role": "assistant", "content": "base自己生成的答案"}
    assert record["messages"][-1]["content"] == "数据集自带答案"
