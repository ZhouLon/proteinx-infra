import numpy as np
from typing import List, Optional, Callable, Dict, Any
from .registry import registry

class BaseVocabProcessor:
    def policy(self) -> Dict[str, Any]:
        raise NotImplementedError
    def encode_batch(self, seqs: List[Optional[str]]) -> List[np.ndarray]:
        p = self.policy()
        id_map: Dict[str, int] = p["id_map"]
        pad_id: int = p["pad_id"]
        unk_id: int = p["unk_id"]
        head_id: int = p["head_id"]
        tail_id: int = p["tail_id"]
        fixed_len_fn: Callable[[int], int] = p.get("fixed_len_fn") or (lambda ml: ml + 2)
        encoded = [[id_map.get(c.upper(), unk_id) for c in (str(s) if s else "")] for s in seqs]
        max_len = max((len(e) for e in encoded), default=0)
        fixed_len = int(fixed_len_fn(max_len))
        out: List[np.ndarray] = []
        for ids in encoded:
            arr = np.full((fixed_len,), pad_id, dtype=np.int32)
            arr[0] = head_id
            if len(ids) > 0:
                arr[1:1+len(ids)] = np.asarray(ids, dtype=np.int32)
            arr[fixed_len-1] = tail_id
            out.append(arr)
        return out

def get_vocab_processor(name: Optional[str]) -> BaseVocabProcessor:
    key = (name or "").strip()
    cls = registry.get_vocab(key)
    return cls()
