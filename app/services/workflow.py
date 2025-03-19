import os
import requests
import json
from config.config import DIFY_CONFIG
from ..utils.logger import logger

class WorkflowService:
    def __init__(self):
        self.api_key = DIFY_CONFIG['api_key_workflow']
        self.base_url = DIFY_CONFIG['base_url']
        
    async def upload_file(self, file_path):
        """上传文件到Dify"""
        try:
            upload_url = f"{self.base_url}/files/upload"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, 'text/plain')
                }
                data = {
                    "user": "system-processor",
                    "type": "TXT"
                }
                
                response = requests.post(upload_url, headers=headers, files=files, data=data)
                response.raise_for_status()
                
                if response.status_code == 201:
                    logger.info(f"文件上传成功: {file_path}")
                    return response.json().get("id")
                else:
                    logger.error(f"文件上传失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"上传文件时发生错误: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"错误响应: {e.response.text}")
            return None
    
    async def run_workflow(self, law_file_path, base_file_path):
        """运行Dify工作流"""
        try:
            # 先上传两个文件
            law_file_id = await self.upload_file(law_file_path)
            base_file_id = await self.upload_file(base_file_path)
            
            if not law_file_id or not base_file_id:
                logger.error("文件上传失败")
                return None
            
            url = f"{self.base_url}/workflows/run"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 组合输入内容
            data = {
                "inputs": {
                    "origin_file": {
                        "transfer_method": "local_file",
                        "upload_file_id": base_file_id,
                        "type": "document"
                    },
                    "Law": {
                        "transfer_method": "local_file",
                        "upload_file_id": law_file_id,
                        "type": "document"
                    }
                },
                "response_mode": "blocking",
                "user": "system-processor"
            }
            

            
            # 发送JSON格式的数据
            response = requests.post(url, headers=headers, json=data)
            
            # 打印响应详情
            # logger.info(f"响应状态码: {response.status_code}")
            # logger.info(f"响应头: {dict(response.headers)}")
            logger.info(f"报错响应内容: {response.text[:500]}...")  # 只打印前500个字符
            
            response.raise_for_status()
            
            result = response.json()
            outputs = result.get('data', {}).get('outputs', {})
            
            if not outputs:
                logger.error("响应中没有找到outputs字段")
                logger.error(f"完整响应: {json.dumps(result, indent=2)}")
                return None
            
            # 获取评估结果并解析
            assessment_result = outputs.get('评估结果')
            if assessment_result:
                try:
                    # 解析JSON字符串
                    assessment_data = json.loads(assessment_result)
                    # 格式化输出
                    formatted_result = f"""
                    评估结果：{assessment_data.get('评估结果', '未知')}
                    法规内容：{assessment_data.get('法规内容', '未知')}
                    检查情况：{assessment_data.get('检查情况', '未知')}
                    评估依据：{assessment_data.get('评估依据', '未知')}
                    """
                    return formatted_result.strip()
                except json.JSONDecodeError as e:
                    # logger.error(f"评估结果解析失败: {str(e)}")
                    return assessment_result  # 如果解析失败，返回原始字符串
            
            logger.error("响应中没有找到评估结果字段")
            logger.error(f"完整响应: {json.dumps(result, indent=2)}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP请求错误: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"错误响应状态码: {e.response.status_code}")
                logger.error(f"错误响应头: {dict(e.response.headers)}")
                logger.error(f"错误响应内容: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"其他错误: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            return None

    async def process_law_files(self):
        """处理Law_list文件夹中的所有文件"""
        try:
            # 确保输出目录存在
            os.makedirs('Judge_output', exist_ok=True)
            
            # 基础文件路径
            base_file_path = os.path.join('knowledge_base', '厂区环境布局.md')
            if not os.path.exists(base_file_path):
                logger.error(f"基础文件不存在: {base_file_path}")
                return False
            
            # 遍历Law_list文件夹
            law_list_dir = 'Law_list'
            for filename in os.listdir(law_list_dir):
                if filename.endswith('.md'):
                    law_file_path = os.path.join(law_list_dir, filename)
                    
                    # 运行工作流
                    logger.info(f"处理文件: {filename}")
                    output_text = await self.run_workflow(law_file_path, base_file_path)
                    
                    if output_text:
                        # 保存输出结果
                        output_path = os.path.join('Judge_output', filename)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(output_text)
                        logger.info(f"已保存输出文件: {output_path}")
                    else:
                        logger.error(f"处理文件 {filename} 失败")
            
            return True
            
        except Exception as e:
            logger.error(f"处理法规文件时发生错误: {str(e)}")
            return False 
        # except Exception as e:
        #     logger.error(f"运行工作流时发生错误: {str(e)}")
        #     if hasattr(e, 'response'):
        #         logger.error(f"错误响应: {e.response.text}")
        #     return None