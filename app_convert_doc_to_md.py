import shutil
from flask import Flask, request, send_file, jsonify
import os
import uuid
import re
import base64
import locale
from pathlib import Path
from werkzeug.utils import secure_filename
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
from openai import OpenAI
import convertapi
from config.config import CONVERT_DOC_TO_MD_CONFIG

# 设置中文本地化环境
locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')

app = Flask(__name__)

# ================== 全局配置 ==================
# 获取当前文件的绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 第三方服务配置
convertapi.api_credentials = CONVERT_DOC_TO_MD_CONFIG['convert_api_credentials'] 
kimi_api_key = CONVERT_DOC_TO_MD_CONFIG['kimi_api_key']
# convertapi.api_credentials = 'secret_HFA4yLSlXBBCZlPe' 
# kimi_api_key = 'sk-3scaeuq5Pvut0jW1d7YsAQV3fkXr3X6rfwk61IEDzgqHUxhG'

# 内存存储任务状态
tasks = {}

# ================== 核心处理函数 ==================
def convert_docx_to_pdf(input_docx, output_dir):
    """DOCX转PDF（增强路径处理版）"""
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        pdf_name = f"{Path(input_docx).stem}.pdf"
        pdf_path = os.path.normpath(os.path.join(output_dir, pdf_name))
        
        print(f"[转换日志] 开始转换 DOCX 到 PDF: {input_docx} → {pdf_path}")
        convertapi.convert('pdf', {'File': input_docx}, from_format='docx').save_files(output_dir)
        return pdf_path
    except Exception as e:
        print(f"[转换错误] DOCX转PDF失败: {str(e)}")
        raise

def process_pdf(pdf_path, output_dir):
    """处理PDF生成Markdown（安全路径版）"""
    try:
        base_name = Path(pdf_path).stem
        image_dir = os.path.normpath(os.path.join(output_dir, "images"))
        md_dir = os.path.normpath(os.path.join(output_dir, base_name))
        
        # 强制创建目录
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(md_dir, exist_ok=True)

        print(f"[处理日志] 开始解析PDF: {pdf_path}")
        print(f"[目录信息] 图片目录: {image_dir}")
        print(f"[目录信息] Markdown目录: {md_dir}")

        # 读取PDF内容
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(pdf_path)
        
        # 处理逻辑
        dataset = PymuDocDataset(pdf_bytes)
        if dataset.classify() == SupportedPdfParseMethod.OCR:
            result = dataset.apply(doc_analyze, ocr=True)
            pipeline = result.pipe_ocr_mode(FileBasedDataWriter(image_dir))
        else:
            result = dataset.apply(doc_analyze, ocr=False)
            pipeline = result.pipe_txt_mode(FileBasedDataWriter(image_dir))
        
        # 生成Markdown文件
        md_file = os.path.normpath(os.path.join(md_dir, f"{base_name}.md"))
        pipeline.dump_md(
            FileBasedDataWriter(md_dir),
            f"{base_name}.md",
            os.path.basename(image_dir)
        )
        return md_file, image_dir
    except Exception as e:
        print(f"[处理错误] PDF处理失败: {str(e)}")
        raise

def analyze_images(md_file, image_dir):
    """图片分析（增强容错版）"""
    try:
        client = OpenAI(
            api_key=kimi_api_key,
            base_url="https://api.moonshot.cn/v1",
            timeout=30  # 增加超时时间
        )
        
        print(f"[分析日志] 开始分析图片: {image_dir}")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        for img_file in os.listdir(image_dir):
            # 过滤非图片文件
            if not img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            # 检查图片是否被引用
            img_ref = f"![]({os.path.basename(image_dir)}/{img_file})"
            if img_ref not in md_content:
                print(f"[分析跳过] 未引用图片: {img_file}")
                continue

            try:
                print(f"[图片处理] 正在处理: {img_file}")
                img_path = os.path.normpath(os.path.join(image_dir, img_file))
                
                # 准备图片数据
                with open(img_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # 调用Kimi API
                response = client.chat.completions.create(
                    model="moonshot-v1-128k-vision-preview",
                    messages=[
                        {"role": "system", "content": "专业图像分析助手，需完整描述所有内容"},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/{Path(img_file).suffix[1:]};base64,{image_data}"
                            }},
                            {"type": "text", "text": "详细描述布局图，重点说明位置关系和空间结构"}
                        ]}
                    ]
                )
                
                # 更新Markdown
                analysis = response.choices[0].message.content
                with open(md_file, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    new_content = content.replace(img_ref, f"{img_ref}\n\n{analysis}")
                    f.seek(0)
                    f.write(new_content)
                    f.truncate()
                
                print(f"[分析完成] 已更新: {img_file}")
                
            except Exception as e:
                print(f"[图片错误] 处理失败 {img_file}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"[分析错误] 图片分析流程失败: {str(e)}")
        raise

# ================== Flask接口 ==================
@app.route('/convert', methods=['POST'])
def handle_convert():
    """文件上传处理接口（增强版）"""
    try:
        # 验证文件上传
        if 'file' not in request.files:
            return jsonify({"error": "未检测到文件上传"}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "空文件名"}), 400
        
        if not file.filename.lower().endswith('.docx'):
            return jsonify({"error": "仅支持DOCX格式"}), 400

        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        task_dir = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], task_id))
        
        try:
            # 创建任务目录
            os.makedirs(task_dir, exist_ok=True)
            print(f"[任务启动] 新建任务目录: {task_dir}")

            # 保存上传文件
            filename = secure_filename(file.filename)
            docx_path = os.path.normpath(os.path.join(task_dir, filename))
            file.save(docx_path)
            print(f"[文件保存] 原始文件路径: {docx_path}")

            # 执行转换流程
            pdf_path = convert_docx_to_pdf(docx_path, task_dir)
            md_file, image_dir = process_pdf(pdf_path, task_dir)
            analyze_images(md_file, image_dir)

            # 记录结果路径
            tasks[task_id] = md_file
            print(f"[任务完成] 最终Markdown路径: {md_file}")
            
            return jsonify({
                "task_id": task_id,
                "download_url": f"/result/{task_id}"
            })
            
        except Exception as e:
            # 清理失败任务
            shutil.rmtree(task_dir, ignore_errors=True)
            print(f"[任务失败] 清理目录: {task_dir}")
            return jsonify({"error": f"处理失败: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500

@app.route('/result/<task_id>')
def get_result(task_id):
    """结果获取接口（增强版）"""
    try:
        if task_id not in tasks:
            return jsonify({"error": "无效任务ID"}), 404
        
        md_path = tasks[task_id]
        if not os.path.exists(md_path):
            return jsonify({"error": "文件不存在"}), 404
            
        return send_file(
            md_path,
            as_attachment=True,
            download_name=os.path.basename(md_path),
            mimetype='text/markdown'
        )
    except Exception as e:
        return jsonify({"error": f"下载失败: {str(e)}"}), 500

# ================== 服务启动 ==================
if __name__ == '__main__':
    # 初始化上传目录
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"[系统启动] 上传目录已创建: {UPLOAD_FOLDER}")
    
    # 启动Flask服务
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,  # 启用多线程
        debug=False    # 生产环境关闭调试模式
    )