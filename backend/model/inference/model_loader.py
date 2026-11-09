import os
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


# ---------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

# Repository root:
# backend/model/inference/model_loader.py
# -> parents[3] = wildfire_assistant/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_ADAPTER_DIR = (
    PROJECT_ROOT
    / "backend"
    / "model"
    / "saved_models"
    / "qwen2.5-0.5b-forestguard-lora"
)

# You can override the adapter location with an environment variable.
ADAPTER_DIR = Path(
    os.getenv("FORESTGUARD_ADAPTER_PATH", str(DEFAULT_ADAPTER_DIR))
).expanduser().resolve()


# ---------------------------------------------------------
# MODEL LOADING
# ---------------------------------------------------------

def load_model():
    """
    Load the original Qwen model and attach the trained
    ForestGuard LoRA adapter.

    CUDA is used when available; otherwise, CPU is used.
    """

    print("=" * 60)
    print("FORESTGUARD AI - MODEL LOADING")
    print("=" * 60)

    # Verify adapter files before loading the base model.
    adapter_config = ADAPTER_DIR / "adapter_config.json"
    adapter_weights = ADAPTER_DIR / "adapter_model.safetensors"

    if not ADAPTER_DIR.is_dir():
        raise FileNotFoundError(
            f"LoRA adapter directory was not found:\n{ADAPTER_DIR}\n\n"
            "Place your adapter files in:\n"
            f"{DEFAULT_ADAPTER_DIR}"
        )

    if not adapter_config.is_file():
        raise FileNotFoundError(
            f"Missing adapter configuration:\n{adapter_config}"
        )

    if not adapter_weights.is_file():
        raise FileNotFoundError(
            f"Missing adapter weights:\n{adapter_weights}"
        )

    # Select device and data type.
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    dtype = (
        torch.float16
        if device.type == "cuda"
        else torch.float32
    )

    print(f"Base model: {MODEL_NAME}")
    print(f"Adapter: {ADAPTER_DIR}")
    print(f"Device: {device}")
    print(f"Data type: {dtype}")

    # -----------------------------------------------------
    # 1. Load tokenizer
    # -----------------------------------------------------

    print("\n[1/3] Loading tokenizer...")

    tokenizer_source = (
        str(ADAPTER_DIR)
        if (ADAPTER_DIR / "tokenizer.json").exists()
        else MODEL_NAME
    )

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_source
    )

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    # -----------------------------------------------------
    # 2. Load original Qwen base model
    # -----------------------------------------------------

    print("\n[2/3] Loading base model...")

    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        dtype=dtype
    )

    base_model.to(device)

    # -----------------------------------------------------
    # 3. Attach ForestGuard LoRA adapter
    # -----------------------------------------------------

    print("\n[3/3] Attaching ForestGuard LoRA adapter...")

    model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_DIR),
        is_trainable=False
    )

    model.eval()

    print("\n" + "=" * 60)
    print("FORESTGUARD MODEL LOADED SUCCESSFULLY")
    print("=" * 60)

    print("Device:", next(model.parameters()).device)
    print("Trainable parameters:", sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    ))

    return model, tokenizer


# ---------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    model, tokenizer = load_model()

    print("\nModel loading test passed.")
    print("Model device:", next(model.parameters()).device)
    print(
        "Total parameters:",
        sum(parameter.numel() for parameter in model.parameters())
    )