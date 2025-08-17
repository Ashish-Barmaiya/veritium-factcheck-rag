from huggingface_hub import HfApi
from app.config import HF_API_KEY

api = HfApi(token=HF_API_KEY)
print(api.whoami())  # Should show your user info