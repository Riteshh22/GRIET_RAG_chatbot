$env:USE_TORCH = "1"
$env:TRANSFORMERS_NO_TF = "1"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
cd "C:\Users\B MADHAVI\hybrid-rag"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
