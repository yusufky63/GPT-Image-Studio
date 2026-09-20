from dataclasses import dataclass
from typing import Optional
@dataclass
class GenerationResult:
    path:str; model:str; prompt:str; width:int; height:int; quality:str; output_format:str
    duration:float; file_size:int
    input_tokens:Optional[int]=None; text_tokens:Optional[int]=None
    image_input_tokens:Optional[int]=None; output_tokens:Optional[int]=None
    total_tokens:Optional[int]=None; cost_usd:Optional[float]=None
    operation:str="generate"; source_path:Optional[str]=None
