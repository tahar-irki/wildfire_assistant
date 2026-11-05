
import torch

from backend.model.inference.model_loader import load_model


SYSTEM_PROMPT = """
You are ForestGuard AI, an educational assistant specialized
in forest fires.

Your responsibilities include explaining:
- Forest fire causes
- Fire prevention
- Fire behavior
- Forest fire detection
- Safety precautions
- Forest ecosystem recovery

Give clear, structured, and scientifically responsible answers.

Do not pretend to predict active fires.
Do not invent emergency information.
For active emergencies, advise users to contact official
emergency services and follow local authorities.
"""


def generate_answer(model, tokenizer, question):
    """
    Generate an answer using the original Qwen model.
    """

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # Convert messages into Qwen's expected chat format.
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True
    )

    # Move input tensors to the same device as the model.
    inputs = {
        key: value.to(next(model.parameters()).device)
        for key, value in inputs.items()
    }

    # Generate new tokens.
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id
        )

    # Remove the original prompt tokens.
    generated_tokens = outputs[
        :, inputs["input_ids"].shape[1]:
    ]

    # Convert generated token IDs into readable text.
    answer = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True
    )[0]

    return answer.strip()


if __name__ == "__main__":

    print("Loading ForestGuard AI baseline model...")

    model, tokenizer = load_model()

    print("\nForestGuard AI is ready!")
    print("Type 'exit' to stop.\n")

    while True:

        question = input("You: ")

        if question.lower().strip() == "exit":
            break

        answer = generate_answer(
            model,
            tokenizer,
            question
        )

        print("\nForestGuard AI:", answer)
        print("-" * 60)
