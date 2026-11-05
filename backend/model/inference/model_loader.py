
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


def load_model():
    """
    Load the original Qwen model and its tokenizer.

    We use CPU for our initial baseline experiment.
    """

    print("Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    print("Loading model...")

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        dtype=torch.float32
    )

    model.eval()

    print("Model loaded successfully!")

    return model, tokenizer


if __name__ == "__main__":
    model, tokenizer = load_model()

    print("\nModel device:", next(model.parameters()).device)
    print("Model parameters:", sum(p.numel() for p in model.parameters()))
