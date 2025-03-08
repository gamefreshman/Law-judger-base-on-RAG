import xml.etree.ElementTree as ET
import json
from ..utils.logger import logger
import requests
import zhipuai
from config.config import ZHIPU_CONFIG

class Graph:
    def __init__(self):
        self.nodes = {}  # 存储节点信息
        self.edges = []  # 存储边信息

    def add_node(self, node_id, attributes):
        self.nodes[node_id] = attributes

    def add_edge(self, source, target, attributes):
        self.edges.append((source, target, attributes))

    def has_node(self, node_id):
        return node_id in self.nodes

    def has_edge(self, source, target):
        return any(edge[0] == source and edge[1] == target for edge in self.edges)

def get_connected_nodes(self, node_id):
    connected_nodes = set()  # 使用集合去重
    visited = set()  # 记录已访问的节点
    queue = [node_id]  # 使用队列进行广度优先搜索

    while queue:
        current_node = queue.pop(0)  # 从队列中取出当前节点
        if current_node not in visited:
            visited.add(current_node)  # 标记当前节点为已访问
            connected_nodes.add(current_node)  # 添加当前节点到连接节点集合

            # 遍历所有边，找到与当前节点相连的节点
            for edge in self.edges:
                if edge[0] == current_node and edge[1] not in visited:
                    queue.append(edge[1])  # 添加目标节点到队列
                elif edge[1] == current_node and edge[0] not in visited:
                    queue.append(edge[0])  # 添加源节点到队列

    return connected_nodes

def load_graph(graphml_file):
    graph = Graph()
    tree = ET.parse(graphml_file)
    root = tree.getroot()

    # 解析节点
    for node in root.findall('.//{http://graphml.graphdrawing.org/xmlns}node'):
        node_id = node.get('id')
        attributes = {}
        for data in node.findall('{http://graphml.graphdrawing.org/xmlns}data'):
            key = data.get('key')
            value = data.text
            attributes[key] = value
        graph.add_node(node_id, attributes)

    # 解析边
    for edge in root.findall('.//{http://graphml.graphdrawing.org/xmlns}edge'):
        source = edge.get('source')
        target = edge.get('target')
        attributes = {}
        for data in edge.findall('{http://graphml.graphdrawing.org/xmlns}data'):
            key = data.get('key')
            value = data.text
            attributes[key] = value
        graph.add_edge(source, target, attributes)

    return graph

def tokenize(text):
    # 调用智谱清言进行分词

            system_prompt = """
            你是一个中文文档分词助手，请根据以下内容进行分词，最后直接返回分词结果，并确保结果是一个列表格式。

            用户输入内容：{tokened_content}
            
            输出示范：["分词结果1", "分词结果2", ...]
            """
            
            # 3. 构建对话历史
            messages = [{"role": "system", "content": system_prompt.format(tokened_content=text)}]
            messages.extend([])
            messages.append({"role": "user", "content": text})
            
            # logger.info("开始调用GLM-4获取分词")
            print(f"发送到GLM-4的消息：{messages}")

            response = zhipuai.ZhipuAI(api_key=ZHIPU_CONFIG['api_key']).chat.completions.create(
                model="glm-4v-plus-0111",
                messages=messages,
                temperature=0.7,
                top_p=0.8,
                max_tokens=1024
            )

            print(f"GLM-4的返回结果：{response.choices[0].message.content}")

            # 处理返回结果
            if response and 'choices' in response and len(response['choices']) > 0:
                result = response['choices'][0]['message']['content']
                # 假设返回的结果是一个 JSON 格式的字符串，解析为 Python 对象
                try:
                    return json.loads(result)  # 返回分词结果
                except json.JSONDecodeError:
                    print("返回结果解析失败")
                    return []
            else:
                print("未能获取有效的响应")
                return []

# 法规库
law_database = [
    "GBZ_T194-2007_4.1.4",
    "GBZ1-2010_5.2.1.3",
    "GB50073-2013_4.2.4",
    "GB50073-2013_4.2.2",
    "GBZ1-2010_5.2.1.4",
    "GBZ_T194-2007_4.1.4"
]

# 示例用法
if __name__ == "__main__":
    # 加载图
    graph_path = r"C:\Users\23757\Desktop\大创相关文档\code_rebuild\PROJECT\Law-judger-base-on-RAG\LightRAG\LawGraph\graph_chunk_entity_relation.graphml"
    graph = load_graph(graph_path)

    # 用户上传的文档路径
    user_document_path = r"C:\Users\23757\Desktop\大创相关文档\code_rebuild\PROJECT\Law-judger-base-on-RAG\knowledge_base\test.md"

    # 读取用户上传的文档
    with open(user_document_path, 'r', encoding='utf-8') as file:
        document_content = file.read()

    # 分词处理
    tokens = tokenize(document_content)

    # 去重
    unique_tokens = set(tokens)

    # 存储评估使用的法规库
    matched_regulations = set()  # 使用集合去重

    # 在获取分词结果后打印
    # print("分词结果:", unique_tokens)

    # 在获取图中节点后打印
    print("图中的节点:", graph.nodes.keys())

    # 对比法规库
    for token in unique_tokens:
        if graph.has_node(token):
            print(f"找到节点: {token}")
            connected_nodes = graph.get_connected_nodes(token)
            print(f"与 {token} 相连的节点: {connected_nodes}")
            for regulation in law_database:
                if regulation in connected_nodes:
                    matched_regulations.add(regulation)
                    print(f"匹配到法规: {regulation}")
        else:
            print(f"未找到节点: {token}")

    # 输出匹配的法规
    print("对该文档评估使用的法规库:", matched_regulations)