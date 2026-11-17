from huggingface_hub import snapshot_download
from pathlib import Path
import os
a = Path(snapshot_download("ResembleAI/chatterbox", allow_patterns=["ve.pt","s3gen.pt","grapheme_mtl_merged_expanded_v1.json","conds.pt","Cangjie5_TC.json"]))
b = Path(snapshot_download("ResembleAI/Chatterbox-Multilingual-es-es", allow_patterns=["t3_es_es.safetensors","s3gen_v3.pt","grapheme_mtl_merged_expanded_v1.json"]))
d = Path("models/cb-es"); d.mkdir(parents=True, exist_ok=True)
for n in ["ve.pt","conds.pt","Cangjie5_TC.json"]:
    (d/n).unlink(missing_ok=True); (d/n).symlink_to(a/n)
for n in ["t3_es_es.safetensors","grapheme_mtl_merged_expanded_v1.json"]:
    (d/n).unlink(missing_ok=True); (d/n).symlink_to(b/n)
(d/"s3gen.pt").unlink(missing_ok=True); (d/"s3gen.pt").symlink_to(b/"s3gen_v3.pt")
(d/"s3gen_v2.pt").unlink(missing_ok=True); (d/"s3gen_v2.pt").symlink_to(a/"s3gen.pt")
print("ok", os.listdir(d))
