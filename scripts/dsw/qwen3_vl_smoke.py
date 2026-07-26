import os

import torch
from PIL import Image, ImageDraw
from modelscope import snapshot_download
from transformers import AutoModelForImageTextToText, AutoProcessor


ROOT = "/mnt/nas/bihaoran/qwen3vl"
MODEL_CACHE = os.path.join(ROOT, "models")
IMAGE_PATH = os.path.join(ROOT, "test_image.png")

os.makedirs(MODEL_CACHE, exist_ok=True)

assert torch.cuda.is_available(), "PPU device is unavailable"

print("torch:", torch.__version__)
print("cuda:", torch.version.cuda)
print("device:", torch.cuda.get_device_name(0))

# 创建本地测试图片，排除网络图片下载问题
image = Image.new("RGB", (256, 256), "white")
draw = ImageDraw.Draw(image)
draw.rectangle((20, 30, 115, 130), fill="red")
draw.ellipse((135, 115, 235, 215), fill="blue")
image.save(IMAGE_PATH)

print("downloading model...")

model_dir = snapshot_download(
    "Qwen/Qwen3-VL-2B-Instruct",
    cache_dir=MODEL_CACHE,
)

print("model_dir:", model_dir)

processor = AutoProcessor.from_pretrained(model_dir)

print("loading model...")

model = AutoModelForImageTextToText.from_pretrained(
    model_dir,
    dtype=torch.bfloat16,
    attn_implementation="sdpa",
    low_cpu_mem_usage=True,
).to("cuda")

messages = [
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

inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt",
)

inputs = {
    key: value.to("cuda") if isinstance(value, torch.Tensor) else value
    for key, value in inputs.items()
}

print("input keys:", list(inputs.keys()))

# 一、多模态推理测试
model.eval()

with torch.inference_mode():
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=48,
        do_sample=False,
    )

input_length = inputs["input_ids"].shape[1]
new_tokens = generated_ids[:, input_length:]

result = processor.batch_decode(
    new_tokens,
    skip_special_tokens=True,
    clean_up_tokenization_spaces=False,
)

print("output:", result[0])
print("INFERENCE_OK")

del generated_ids, new_tokens
torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()

# 二、训练损失和反向传播测试
model.train()
model.config.use_cache = False
model.zero_grad(set_to_none=True)

labels = inputs["input_ids"].clone()
labels[inputs["attention_mask"] == 0] = -100

outputs = model(
    **inputs,
    labels=labels,
)

loss = outputs.loss
print("loss:", float(loss.detach().cpu()))

if not torch.isfinite(loss):
    raise RuntimeError("Loss is not finite")

loss.backward()

grad_name = None
grad_value = None

for name, parameter in model.named_parameters():
    if parameter.grad is not None:
        grad_name = name
        grad_value = parameter.grad
        break

if grad_name is None:
    raise RuntimeError("No parameter gradient was generated")

if not torch.isfinite(grad_value).all():
    raise RuntimeError(f"Non-finite gradient detected: {grad_name}")

print("first_gradient:", grad_name)
print("BACKWARD_OK")
print(
    "peak_memory_gb:",
    round(torch.cuda.max_memory_allocated() / 1024**3, 2),
)
