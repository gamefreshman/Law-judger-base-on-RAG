import os
import logging
from lightrag import LightRAG, QueryParam
from lightrag.llm import zhipu_complete, zhipu_embedding
from lightrag.utils import EmbeddingFunc

import networkx as nx
from pyvis.network import Network
import random

WORKING_DIR = "C:\\Users\\23757\\Desktop\\大创相关文档\\code_rebuild\\PROJECT\\Law-judger-base-on-RAG\\knowledge_base"

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

os.environ["ZHIPU_API_KEY"] = "ebf92b371240de59a53a89d53d80dbe6.6QvONTjyLvlsqNOt"

api_key = os.environ.get("ZHIPU_API_KEY")

print(api_key)

# api_key = "ebf92b371240de59a53a89d53d80dbe6.6QvONTjyLvlsqNOt"
if api_key is None:
    raise Exception("Please set ZHIPU_API_KEY in your environment")


rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=zhipu_complete,
    llm_model_name="glm-4v-plus-0111",  # Using the most cost/performance balance model, but you can change it here.
    llm_model_max_async=4,
    llm_model_max_token_size=32768,
    embedding_func=EmbeddingFunc(
        embedding_dim=2048,  # Zhipu embedding-3 dimension
        max_token_size=8192,
        func=lambda texts: zhipu_embedding(texts),
    ),
)

with open("C:\\Users\\23757\\Desktop\\大创相关文档\\code_rebuild\\PROJECT\\Law-judger-base-on-RAG\\knowledge_base\\dify知识库.md", "r", encoding="utf-8") as f:rag.insert(f.read())

G = nx.read_graphml("C:\\Users\\23757\\Desktop\\大创相关文档\\code_rebuild\\PROJECT\\Law-judger-base-on-RAG\\knowledge_base\\graph_chunk_entity_relation.graphml")

net = Network(height="100vh", notebook=True)

net.from_nx(G)

for node in net.nodes:
    node["color"] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    if "description" in node:
        node["title"] = node["description"]

for edge in net.edges:
    if "description" in edge:
        edge["title"] = edge["description"]

net.show("knowledge_graph.html")
# # Perform naive search
# print(
#     rag.query("What are the top themes in this story?", param=QueryParam(mode="naive"))
# )

# # Perform local search
# print(
#     rag.query("What are the top themes in this story?", param=QueryParam(mode="local"))
# )

# # Perform global search
# print(
#     rag.query("What are the top themes in this story?", param=QueryParam(mode="global"))
# )

# # Perform hybrid search
# print(
#     rag.query("What are the top themes in this story?", param=QueryParam(mode="hybrid"))
# )

# Perform naive search
print(
    rag.query("文本内容的主题是什么？", param=QueryParam(mode="naive"))
)

# Perform local search
print(
    rag.query("文本内容的主题是什么？", param=QueryParam(mode="local"))
)

# Perform global search
print(
    rag.query("文本内容的主题是什么？", param=QueryParam(mode="global"))
)

# Perform hybrid search
print(
    rag.query("文本内容的主题是什么？", param=QueryParam(mode="hybrid"))
)

# stream response 这个模块有点问题
resp = rag.query(
    "文本内容的主题是什么？",
    param=QueryParam(mode="hybrid", stream=True),
)