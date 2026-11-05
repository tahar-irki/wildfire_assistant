
from backend.model.inference.model_loader import load_model

model, tokenizer = load_model()

print("\n========== MODEL CONFIGURATION ==========")

config = model.config

print("Model type:", config.model_type)
print("Vocabulary size:", config.vocab_size)
print("Hidden size:", config.hidden_size)
print("Number of Transformer layers:", config.num_hidden_layers)
print("Number of attention heads:", config.num_attention_heads)
print("Number of key/value heads:", config.num_key_value_heads)
print("Intermediate size:", config.intermediate_size)
print("Maximum positions:", config.max_position_embeddings)

print("\n========== MODEL STRUCTURE ==========")

print(model)

print("\n========== PARAMETER COUNT ==========")

total_parameters = sum(
    parameter.numel()
    for parameter in model.parameters()
)

print(f"Total parameters: {total_parameters:,}")

print("\n========== EMBEDDING SHAPE ==========")

print(model.model.embed_tokens.weight.shape)

print("\n========== FIRST TRANSFORMER LAYER ==========")

print(model.model.layers[0])
