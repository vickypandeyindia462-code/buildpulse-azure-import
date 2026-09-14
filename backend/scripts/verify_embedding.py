from backend.app.embeddings import get_embedding, provider, EMBEDDING_DIM
import json

print('provider:', provider)
vec = get_embedding('verify provider')
print('len:', len(vec))
print('sample:', json.dumps(vec[:6]))
