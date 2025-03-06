import requests
import json
import os
import glob
from config.config import DIFY_CONFIG, FILE_CONFIG
from ..utils.logger import logger
from .workflow import WorkflowService

import subprocess

class DocumentService:
    def __init__(self):
        self.api_key = DIFY_CONFIG['api_key']
        self.dataset_id = DIFY_CONFIG['dataset_id']
        self.base_url = DIFY_CONFIG['base_url']
        self.workflow_service = WorkflowService()
        self.converter_url = "http://127.0.0.1:5000"
    
    def _clean_knowledge_base(self):
        """清理knowledge_base文件夹，只保留最新文件"""
        knowledge_base_dir = FILE_CONFIG['upload_dir']
        files = glob.glob(os.path.join(knowledge_base_dir, '*'))
        for file in files:
            try:
                os.remove(file)
                logger.info(f"已删除旧文件: {file}")
            except Exception as e:
                logger.error(f"删除文件失败: {file}, 错误: {str(e)}")
    
    def _decode_content(self, content):
        """尝试使用不同编码解码文件内容"""
        encodings = ['utf-8', 'gbk', 'gb18030', 'big5', 'latin1']
        
        for encoding in encodings:
            try:
                text_content = content.decode(encoding)
                logger.info(f"成功使用 {encoding} 解码文件")
                return text_content
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，尝试使用errors='ignore'
        logger.warning("所有编码尝试失败，使用ignore模式解码")
        return content.decode('utf-8', errors='ignore')
    
    async def convert_docx_to_md(self, filename, content):
        """将docx文件转换为markdown格式"""
        try:
            logger.info(f"开始转换文件: {filename}")
            logger.info(f"转换服务URL: {self.converter_url}/convert")
            
            # 发送转换请求
            convert_request = requests.post(
                f'{self.converter_url}/convert',
                files={'file': (filename, content)}
            )

             # 添加调试信息
            print(f"Response status code: {convert_request.status_code}")
            print(f"Response content: {convert_request.text}")

            convert_request.raise_for_status()
            # convert_info = convert_request.content
            response_data = convert_request.json()
            task_id = response_data.get('task_id')

            if not task_id:
                self.set_status(500)
                self.write({
                    "status": "error",
                    "message": "转换服务task_id获取失败"
                })
                return

            convert_response = requests.get(f'http://127.0.0.1:5000/result/{task_id}')
            
            # 记录响应信息
            logger.info(f"转换服务响应状态码: {convert_response.status_code}")
            
            convert_response.raise_for_status()
            
            # 直接获取响应文本作为markdown内容
            md_content = convert_response.text
            
            if not md_content:
                raise ValueError("转换服务返回的Markdown内容为空")
            
            logger.info("文件转换成功")
            logger.info(f"转换后的内容长度: {len(md_content)} 字符")
            return md_content
            
        except requests.RequestException as e:
            logger.error(f"请求转换服务失败: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"错误响应: {e.response.text}")
            raise ValueError(f"转换服务请求失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"转换docx文件失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: \n{traceback.format_exc()}")
            raise
    
    async def upload_document(self, file_info):
        """上传文档到Dify并进行法规评估"""
        try:
            # 清理knowledge_base文件夹
            self._clean_knowledge_base()
            
            filename = file_info['filename']
            content = file_info['body']
            
            # 处理.docx文件
            if filename.lower().endswith('.docx'):
                logger.info(f"检测到docx文件: {filename}，开始转换")
                md_content = await self.convert_docx_to_md(filename, content)
                filename = filename.replace('.docx', '.md')
                content = md_content.encode('utf-8')
                logger.info(f"docx文件转换完成，新文件名: {filename}")
            
            # 保存文件
            file_path = os.path.join(FILE_CONFIG['upload_dir'], filename)
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"已保存文件到knowledge_base: {filename}")
            
            # 解码文件内容
            text_content = self._decode_content(content)
            
            # 上传到Dify知识库
            url = f"{self.base_url}/datasets/{self.dataset_id}/document/create-by-text"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "name": filename,
                "text": text_content,
                "indexing_technique": "high_quality",
                "process_rule": {
                    "mode": "automatic"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"文件已上传到Dify知识库: {filename}")

            # 获取评估使用的法规
            script_path = r"C:\Users\23757\Desktop\大创相关文档\code_rebuild\PROJECT\Law-judger-base-on-RAG\LightRAG\lightrag_zhipu_demo.py"
            python_executable = r"C:\Positive\env\VM\anaconda\envs\MinerU\python.exe"
            
            # 打印调试信息
            print(f"Python 解释器路径: {python_executable}")
            print(f"脚本路径: {script_path}")
            

            # 执行脚本
            subprocess.run([python_executable, script_path], check=True)     

            # 读取 LawList.txt 文件中的法规名称
            law_names = []
            with open("LawList.txt", "r", encoding="utf-8") as law_file:
                law_names = [line.strip() for line in law_file.readlines()]
            
            # 进行法规评估
            law_list_dir = 'Law_list'
            os.makedirs('Judge_output', exist_ok=True)
            
            assessment_results = []
            for law_name in law_names:
                law_file = f"{law_name}.md"
                law_file_path = os.path.join(law_list_dir, law_file)

                if os.path.exists(law_file_path):
                    logger.info(f"正在评估文件 {filename} 与法规 {law_file}")
                    output_text = await self.workflow_service.run_workflow(law_file_path, file_path)
                    
                    if output_text:
                        assessment_results.append({
                            'law_file': law_file,
                            'assessment': output_text
                        })

                        output_path = os.path.join('Judge_output', f"{law_file}")
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(output_text)
                        logger.info(f"已保存评估结果: {output_path}")
                else:
                    logger.warning(f"法规文件不存在: {law_file_path}, 跳过评估")

            return {
                'upload_status': 'success',
                'upload_response': response.json(),
                'assessments': assessment_results
            }
            
        except Exception as e:
            logger.error(f"处理文件时发生错误: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            
        #     for law_file in os.listdir(law_list_dir):
        #         if law_file.endswith('.md'):
        #             law_file_path = os.path.join(law_list_dir, law_file)
        #             logger.info(f"正在评估文件 {filename} 与法规 {law_file}")
        #             output_text = await self.workflow_service.run_workflow(law_file_path, file_path)
                    
        #             if output_text:
        #                 assessment_results.append({
        #                     'law_file': law_file,
        #                     'assessment': output_text
        #                 })
                        
        #                 output_path = os.path.join('Judge_output', f"{law_file}")
        #                 with open(output_path, 'w', encoding='utf-8') as f:
        #                     f.write(output_text)
        #                 logger.info(f"已保存评估结果: {output_path}")
            
        #     return {
        #         'upload_status': 'success',
        #         'upload_response': response.json(),
        #         'assessments': assessment_results
        #     }
            
        # except Exception as e:
        #     logger.error(f"处理文件时发生错误: {str(e)}")
        #     logger.error(f"错误类型: {type(e).__name__}")
        #     import traceback
        #     logger.error(f"错误堆栈: \n{traceback.format_exc()}")
        #     return None
    
    async def get_documents(self):
        """获取文档列表"""
        try:
            url = f"{self.base_url}/datasets/{self.dataset_id}/documents"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"获取文档列表时发生错误: {str(e)}")
            return None 