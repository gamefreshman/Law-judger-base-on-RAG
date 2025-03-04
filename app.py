from datetime import datetime
import subprocess
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import sys
import traceback
from typing import Optional, Dict, Any
from pydantic import BaseModel
import json
from fastapi.responses import HTMLResponse

class ChatResponse(BaseModel):
    code: int
    answer: str
    metadata: Dict[str, Any]
    knowledge_base_content: str
    timestamp: str
class ChatRequest(BaseModel):
    query: str
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 修改导入语句
from app.services.chat import ChatService
from app.services.document import DocumentService
from config.config import FILE_CONFIG
from app.utils.logger import logger

# 创建FastAPI应用
app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:3000"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取项目根目录
root_dir = os.path.dirname(os.path.abspath(__file__))

# 创建服务实例
chat_service = ChatService()
document_service = DocumentService()


@app.get("/run-script", response_class=HTMLResponse)
async def run_script():
    script_path = r"C:\Users\23757\Desktop\大创相关文档\code_rebuild\PROJECT\Law-judger-base-on-RAG\LightRAG\lightrag_zhipu_demo.py"
    python_executable = r"C:\Positive\env\VM\anaconda\envs\MinerU\python.exe"
    
    # 打印调试信息
    print(f"Python 解释器路径: {python_executable}")
    print(f"脚本路径: {script_path}")
    
    try:
        # 执行脚本
        subprocess.run([python_executable, script_path], check=True)
        
        # 读取生成的 HTML 文件
        with open("knowledge_graph.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    
    except FileNotFoundError as e:
        return HTMLResponse(content=f"文件未找到: {str(e)}", status_code=500)
    except Exception as e:
        return HTMLResponse(content=f"执行脚本时发生错误: {str(e)}", status_code=500)

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "success",
        "message": "Server is running",
        "service": "chat-service",
        "version": "1.0.0"
    }
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        if not request.query:
            return JSONResponse(
                status_code=400,
                content={
                    "code": 400,
                    "message": "查询内容不能为空"
                }
            )
           
        # 调用知识库服务获取回答
        try:
            response = await chat_service.retrieve_knowledge(request.query)
        except Exception as service_error:
            print(f"Knowledge service error: {str(service_error)}")
            response = str(service_error)

        # 从response中提取知识库内容
        knowledge_content = ""
        answer_content = ""

        # 处理不同类型的响应
        if isinstance(response, dict):
            # 如果response是字典格式
            if "data" in response and isinstance(response["data"], dict):
                data = response["data"]
                if "data" in data and isinstance(data["data"], dict):
                    inner_data = data["data"]
                    answer_content = inner_data.get("answer", "")
                    knowledge_content = inner_data.get("knowledge_base_content", "")
                else:
                    answer_content = data.get("answer", "")
                    knowledge_content = data.get("knowledge_base_content", "")
            else:
                answer_content = response.get("answer", "")
                knowledge_content = response.get("knowledge_base_content", "")
        else:
            # 如果response是字符串
            answer_content = str(response)

        # 构造响应数据
        response_data = {
            "code": 200,
            "answer": answer_content,
            "metadata": {
                "model": "glm-4-flash",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            },
            "knowledge_base_content": knowledge_content,
            "timestamp": datetime.now().isoformat()
        }

        return JSONResponse(content=response_data)
       
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        error_response = {
            "code": 500,
            "message": str(e)
        }
        return JSONResponse(
            status_code=500,
            content=error_response
        )

# 错误处理中间件
@app.middleware("http")
async def error_handling_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Middleware caught error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": str(e)
            }
        )
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "没有找到上传的文件"
                }
            )
        filename = file.filename
        
        # 确保文件名是UTF-8编码
        try:
            filename = filename.encode('latin1').decode('utf-8')
        except UnicodeError:
            try:
                filename = filename.encode('latin1').decode('gbk')
            except UnicodeError:
                filename = filename  # 保持原样
        
        logger.info(f"处理上传文件: {filename}")
        
        # 确保目录存在
        os.makedirs(FILE_CONFIG['upload_dir'], exist_ok=True)
        
        # 保存上传的文件
        file_path = os.path.join(FILE_CONFIG['upload_dir'], filename)
        file_content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"文件已保存到: {file_path}")
        
        # 创建文件信息字典，模拟tornado的文件信息格式
        file_info = {
            'filename': filename,
            'body': file_content,
            'content_type': file.content_type
        }
        
        # 上传到Dify并进行法规评估
        result = await document_service.upload_document(file_info) 

        # 读取Judge_output文件夹中的所有文件
        judge_output_path = os.path.join(root_dir, 'good_output')
        judged_content: Dict[str, str] = {}
        
        if os.path.exists(judge_output_path):
            file_count = 0
            for file_name in os.listdir(judge_output_path):
                if os.path.isfile(os.path.join(judge_output_path, file_name)):
                    file_count += 1
                    # 获取文件名（不含扩展名）
                    file_base_name = os.path.splitext(file_name)[0]
                    
                    # 读取文件内容
                    try:
                        with open(os.path.join(judge_output_path, file_name), 'r', encoding='utf-8') as f:
                            content = f.read()
                            judged_content[file_base_name] = content
                    except Exception as e:
                        logger.error(f"读取文件 {file_name} 时发生错误: {str(e)}")
                        continue
            
            return {
                "status": "success",
                "message": "文件上传并完成法规评估",
                "data": {
                    "law_num": file_count,
                    "judged_content": judged_content
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Judge_output文件夹不存在"
                }
            )
            
    except Exception as e:
        logger.error(f"处理上传请求时发生错误: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误堆栈: \n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"文件处理错误: {str(e)}"
            }
        )

@app.get("/api/documents")
async def get_documents():
    try:
        documents = await document_service.get_documents()
        
        if documents:
            return {
                "status": "success",
                "data": documents
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "获取文档列表失败"
                }
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e)
            }
        )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "请求的资源不存在"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误"}
    )

if __name__ == "__main__":
    try:
        # 检查关键目录和文件
        template_dir = os.path.join(root_dir, "templates")
        index_file = os.path.join(template_dir, "index.html")
        
        logger.info("="*50)
        logger.info("服务器启动检查")
        logger.info(f"项目根目录: {root_dir}")
        # 启动服务器
        port = 8888
        logger.info(f"服务器启动成功: http://localhost:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error("="*50)
        logger.error("服务器启动失败")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误信息: {str(e)}")
        logger.error(f"错误堆栈: \n{traceback.format_exc()}")
        sys.exit(1)