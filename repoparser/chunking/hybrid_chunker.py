# from pathlib import Path
# from typing import List

# from .ast_chunker import extract_ast_chunks
# from .ts_chunker import extract_ts_chunks
# from .chunk_schema import CodeChunk


# def hybrid_chunk_file(file_path: Path) -> List[CodeChunk]:
#     ast_chunks = extract_ast_chunks(file_path)
#     ts_chunks = extract_ts_chunks(file_path)

#     ts_by_lines = {
#         (c.span.start_line, c.span.end_line): c
#         for c in ts_chunks
#         if c.span.start_line is not None and c.span.end_line is not None
#     }

#     for ast_chunk in ast_chunks:
#         if ast_chunk.span.start_line is None or ast_chunk.span.end_line is None:
#             continue

#         key = (ast_chunk.span.start_line, ast_chunk.span.end_line)

#         ts_chunk = ts_by_lines.get(key)
#         if ts_chunk:
#             ast_chunk.span.start_byte = ts_chunk.span.start_byte
#             ast_chunk.span.end_byte = ts_chunk.span.end_byte

#     return ast_chunks
