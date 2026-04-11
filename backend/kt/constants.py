import torch

QUE_TYPE_MODELS = ["iekt", "qdkt"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


SEQ_LEN_MODELS = [
    "saint",
    "saint++",
    "sakt",
    "atdkt",
    "simplekt",
    "stablekt",
    "datakt",
    "folibikt",
]
