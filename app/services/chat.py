import zhipuai
import requests
import json
from config.config import ZHIPU_CONFIG, DIFY_CONFIG, RETRIEVAL_CONFIG
from ..utils.logger import logger

class ChatService:
    def __init__(self):
        self.client = zhipuai.ZhipuAI(api_key=ZHIPU_CONFIG['api_key'])
        self.model = "glm-4-flash"
        self.chat_history = []
        
    def format_response(self, response_data):
        """格式化响应数据以供前端显示"""
        if not response_data:
            return {
                'code': 500,
                'message': '处理请求时出现错误',
                'data': {
                    'answer': '抱歉，处理您的请求时出现错误。',
                    'metadata': None,
                    'chat_history': [],
                    'knowledge_base_content': None
                }
            }
            
       
        return {
            'code': 200,
            'message': 'success',
            'data': {
                'answer': response_data.get('answer', ''),
                'metadata': response_data.get('metadata', {}),
                'chat_history': response_data.get('chat_history', []),
                'knowledge_base_content': response_data.get('knowledge_base_content', '')
            }
        }
        
    async def search_knowledge_base(self, query):
        """从Dify知识库中检索相关内容"""
        try:
            # 1. 使用简单的检索请求
            retrieve_url = f"{DIFY_CONFIG['base_url']}/datasets/{DIFY_CONFIG['dataset_id']}/retrieve"
            headers = {
                'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            
            retrieve_data = {
                "query": query,
                "top_k": 3
            }
            
            logger.info(f"发送检索请求: URL={retrieve_url}")
            logger.info(f"请求数据: {retrieve_data}")
            
            response = requests.post(retrieve_url, headers=headers, json=retrieve_data)
            response.raise_for_status()
            
            retrieve_result = response.json()
            logger.info(f"检索响应: {retrieve_result}")
            
            # 构建上下文
            context = ""
            if 'records' in retrieve_result:
                for record in retrieve_result['records']:
                    if 'segment' in record:
                        segment = record['segment']
                        doc_name = segment.get('document', {}).get('name', '未知文档')
                        content = segment.get('content', '')
                        score = record.get('score', 0)
                        context += f"\n来自文档 '{doc_name}' (相关度: {score:.4f}):\n{content}\n"
            
            return context if context else "未找到相关内容"
            
        except Exception as e:
            logger.error(f"检索知识库时发生错误: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"错误响应: {e.response.text}")
            return "知识库检索失败"
    
    async def retrieve_knowledge(self, query):
        """使用GLM-4进行知识库问答"""
        try:
            # 1. 检索知识库
            logger.info(f"开始检索知识库，查询：{query}")
            knowledge_content = await self.search_knowledge_base(query)
            logger.info(f"知识库检索结果：{knowledge_content}")
            
            # 2. 构建系统提示语
            system_prompt = """
你是一个工业企业设计标准知识库的助手。请按以下步骤处理用户问题：
1. 分析用户问题的关键点
2. 根据知识库检索内容提供专业答案
3. 引用相关标准和规范
4. 保持回答简洁清晰

知识库检索结果如下：
{knowledge_base_content}

请基于以上检索内容，结合你的专业知识，给出完整的回答。如果检索内容不足以回答问题，请明确说明。
            """
            
            # 3. 构建对话历史
            messages = [{"role": "system", "content": system_prompt.format(knowledge_base_content=knowledge_content)}]
            messages.extend(self.chat_history)
            messages.append({"role": "user", "content": query})
            
            logger.info("开始调用GLM-4获取初步回答")
            logger.info(f"发送到GLM-4的消息：{messages}")
            
            # 4. 调用GLM-4获取初步回答
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                top_p=0.8,
                max_tokens=1500
            )
            
            initial_answer = response.choices[0].message.content
            logger.info(f"GLM-4初步回答：{initial_answer}")
            
            # 5. 使用GLM-4进行答案优化
            optimization_prompt = f"""
请作为专业的工业设计顾问，审查并优化以下回答：

原始问题：{query}

知识库内容：
{knowledge_content}

初步回答：
{initial_answer}

请按以下方面优化回答：
1. 确保回答准确性和专业性
2. 补充必要的技术细节
3. 添加相关的标准规范引用
4. 使表述更加清晰和结构化
5. 如果知识库内容不足，建议其他参考来源

优化后的回答："""

            logger.info("开始优化回答")
            optimization_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": optimization_prompt}],
                temperature=0.5,
                top_p=0.9,
                max_tokens=2000
            )
            
            optimized_answer = optimization_response.choices[0].message.content
            logger.info(f"优化后的回答：{optimized_answer}")
            
            # 6. 更新对话历史
            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": optimized_answer})
            
            # 7. 保持对话历史在合理长度
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            # 8. 构建响应数据
            response_data = {
                'answer': optimized_answer,
                'metadata': {
                    'model': self.model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens + optimization_response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens + optimization_response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens + optimization_response.usage.total_tokens
                    }
                },
                'chat_history': self.chat_history,
                'knowledge_base_content': knowledge_content
            }
            
            logger.info(f"构建的响应数据：{response_data}")
            formatted_response = self.format_response(response_data)
            logger.info(f"格式化后的响应：{formatted_response}")
            return formatted_response
                
        except Exception as e:
            logger.error(f"调用智谱AI时发生错误: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"错误响应: {e.response}")
            error_response = self.format_response(None)
            logger.error(f"返回错误响应：{error_response}")
            return error_response
            
    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []