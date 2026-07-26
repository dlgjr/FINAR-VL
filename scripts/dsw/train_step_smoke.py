import os

import torch
from PIL import Image, ImageDraw
from transformers import AutoModelForImageTextToText, AutoProcessor


ROOT = "/mnt/nas/bihaoran/qwen3vl"
MODEL_DIR = (
    f"{ROOT}/models/models/"
    "Qwen--Qwen3-VL-2B-Instruct/snapshots/master"
)
IMAGE_PATH = f"{ROOT}/test_image.png"

os.makedirs(f"{ROOT}/logs", exist_ok=True)

if not os.path.exists(IMAGE_PATH):
    image = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 30, 115, 130), fill="red")
    draw.ellipse((135, 115, 235, 215), fill="blue")
    image.save(IMAGE_PATH)

processor = AutoProcessor.from_pretrained(
    MODEL_DIR,
    local_files_only=True,
)

model = AutoModelForImageTextToText.from_pretrained(
    MODEL_DIR,
    dtype=torch.bfloat16,
    attn_implementation="sdpa",
    low_cpu_mem_usage=True,
    local_files_only=True,
).to("cuda")

model.config.use_cache = False
model.train()

user_messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "image": IMAGE_PATH,
                "resized_height": 256,
                "resized_width": 256,
            },
            {
                "type": "text",
                "text": "请描述图片中的图形和颜色。",
            },
        ],
    }
]

full_messages = user_messages + [
    {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "图片中有一个红色正方形和一个蓝色圆形，背景为白色。",
            }
        ],
    }
]

prompt_inputs = processor.apply_chat_template(
    user_messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt",
)

batch = processor.apply_chat_template(
    full_messages,
    tokenize=True,
    add_generation_prompt=False,
    return_dict=True,
    return_tensors="pt",
)

prompt_length = prompt_inputs["input_ids"].shape[1]

batch = {
    key: value.to("cuda") if isinstance(value, torch.Tensor) else value
    for key, value in batch.items()
}

labels = batch["input_ids"].clone()
labels[:, :prompt_length] = -100
labels[batch["attention_mask"] == 0] = -100
batch["labels"] = labels

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.95),
    weight_decay=0.0,
    foreach=False,
    fused=False,
)

torch.cuda.reset_peak_memory_stats()
losses = []

for step in range(1, 4):
    optimizer.zero_grad(set_to_none=True)

    outputs = model(**batch)
    loss = outputs.loss

    if not torch.isfinite(loss):
        raise RuntimeError(f"step {step}: non-finite loss")

    loss.backward()

    tracked_name = None
    tracked_parameter = None

    for name, parameter in model.named_parameters():
        if parameter.grad is not None:
            if parameter.grad.detach().abs().max().item() > 0:
                tracked_name = name
                tracked_parameter = parameter
                break

    if tracked_parameter is None:
        raise RuntimeError("No non-zero gradient found")

    before = tracked_parameter.detach().float().clone()
    optimizer.step()

    max_update = (
        tracked_parameter.detach().float() - before
    ).abs().max().item()

    loss_value = loss.detach().float().cpu().item()
    losses.append(loss_value)

    print(
        f"step={step} "
        f"loss={loss_value:.6f} "
        f"parameter={tracked_name} "
        f"max_update={max_update:.8f}"
    )

    if max_update == 0:
        raise RuntimeError("Optimizer step did not update parameters")

print("losses:", losses)
print(
    "peak_memory_gb:",
    round(torch.cuda.max_memory_allocated() / 1024**3, 2),
)
print("TRAINING_STEP_OK")
