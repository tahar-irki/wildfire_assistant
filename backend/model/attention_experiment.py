
from backend.model.inference.model_loader import load_model

model, tokenizer = load_model()

# Get the first Transformer layer
layer = model.model.layers[0]

print("\n========== ATTENTION PROJECTIONS ==========")

attention = layer.self_attn

for name, module in attention.named_children():

    if hasattr(module, "weight"):
        print(
            f"{name}: "
            f"{tuple(module.weight.shape)}"
        )

print("\n========== ATTENTION HEAD INFORMATION ==========")

config = model.config

head_dim = config.hidden_size // config.num_attention_heads

print("Hidden size:", config.hidden_size)
print("Query heads:", config.num_attention_heads)
print("Key/value heads:", config.num_key_value_heads)
print("Head dimension:", head_dim)

print(
    "Query projection output:",
    attention.q_proj.out_features
)

print(
    "Key projection output:",
    attention.k_proj.out_features
)

print(
    "Value projection output:",
    attention.v_proj.out_features
)

print("\n========== MLP INFORMATION ==========")

mlp = layer.mlp

for name, module in mlp.named_children():

    if hasattr(module, "weight"):
        print(
            f"{name}: "
            f"{tuple(module.weight.shape)}"
        )

print("\n========== PARAMETER COUNTS ==========")

def count_parameters(module):
    return sum(p.numel() for p in module.parameters())

print(
    "Attention parameters:",
    f"{count_parameters(attention):,}"
)

print(
    "MLP parameters:",
    f"{count_parameters(mlp):,}"
)

print(
    "Complete first layer parameters:",
    f"{count_parameters(layer):,}"
)
