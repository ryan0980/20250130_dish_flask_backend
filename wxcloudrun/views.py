from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import time
from together import Together  # 需要先安装 together 包
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/api/analyze_menu', methods=['POST'])
def analyze_menu():
    """
    分析菜单图片并返回结构化数据
    :return: 返回分析结果
    """
    try:
        # 获取请求体参数
        params = request.get_json()
        
        if 'image' not in params:
            return make_err_response('缺少image参数')
            
        # 获取base64图片数据
        image_base64 = params['image']
        print("\n=== API Request Debug Info ===")
        print(f"Image base64 prefix: {image_base64[:50]}...")
        
        # 记录开始时间
        start_time = time.time()
        
        # 初始化Together客户端
        client = Together(
            api_key="43a055c9202a487b90992dbc228455059cc9b36ad010dce5372f7b30a04ee0c6"
        )
        
        # 设置提示语
        system_prompt = """
        You are given an image of a menu. Your job is to extract all the menu items and present them in the following format:

        Name | Description | Price | Category

        Category numbers:
        1: Appetizers (前菜、凉菜)
        2: Main Dishes (主菜、热菜)
        3: Soups (汤类)
        4: Rice & Noodles (主食、面食)
        5: Desserts (甜点)
        6: Beverages (饮品)
        7: Others (其他)

        Formatting guidelines:
        1. Each menu item must be presented on a separate line.
        2. Do not include empty lines between items.
        3. Use the separator " | " (pipe with spaces) to separate fields.
        4. If a description or price is missing, replace it with the word "null".
        5. Category must be a number from 1-7 as defined above.
        6. Do not add any extra text, explanations, or formatting.

        Example output:
        Spring Rolls | Crispy vegetable rolls with sweet chili sauce | 8 | 1
        Kung Pao Chicken | Spicy diced chicken with peanuts | 15 | 2
        Hot and Sour Soup | Traditional Chinese soup | 6 | 3
        Fried Rice | With eggs and vegetables | 12 | 4
        Mango Pudding | Fresh mango flavor | 6 | 5
        Green Tea | Hot or cold | 3 | 6
        Extra Sauce | Choice of sauces | 1 | 7
        """
        
        print("\n=== API Call Info ===")
        print(f"Model: meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo")
        print(f"Max tokens: 4096")
        
        # 调用API
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ],
                }
            ],
            max_tokens=4096
        )
        
        # 处理API返回的结果
        menu_text = response.choices[0].message.content.strip()
        menu_items = menu_text.split('\n')
        
        print("\n=== Menu Text ===")
        print(menu_text)
        
        # 按类别分类
        categorized_items = {
            "1": [],  # Appetizers
            "2": [],  # Main Dishes
            "3": [],  # Soups
            "4": [],  # Rice & Noodles
            "5": [],  # Desserts
            "6": [],  # Beverages
            "7": []   # Others
        }
        
        # 先按类别分类，添加错误处理
        for item in menu_items:
            try:
                parts = item.split(" | ")
                if len(parts) == 4:  # 确保格式正确
                    name, desc, price, category = parts
                    # 清理category字符串，只保留数字
                    category = ''.join(filter(str.isdigit, category))
                    # 确保category在有效范围内
                    if category in categorized_items:
                        categorized_items[category].append([name, desc, price])
                    else:
                        print(f"Warning: Invalid category '{category}' for item '{name}'")
                else:
                    print(f"Warning: Invalid format for item: {item}")
            except Exception as item_error:
                print(f"Warning: Error processing item '{item}': {str(item_error)}")
                continue
        
        # 构建翻译提示
        translate_prompt = """
        将以下菜品信息完全翻译成中文，包括菜品名称。格式：中文菜名 | 中文描述 | 价格 | 类别编号

        特别注意：
        1. 菜品名称必须翻译成标准中文菜名，例如：
           - Kung Pao Chicken → 宫保鸡丁
           - Mapo Tofu → 麻婆豆腐
           - Dry-Fried Green Beans → 干煸四季豆
        2. 描述部分要用地道的中文烹饪术语，例如：
           - stir-fried → 翻炒
           - crispy → 酥脆
           - spicy → 麻辣/辣味

        格式要求：
        1. 严格使用 " | " 作为分隔符（含两边空格）
        2. 每个菜品占一行，不要有空行
        3. 价格保持数字不变
        4. 如果是"null"保持不变
        5. 类别编号保持不变
        6. 不要添加任何额外内容

        正确示例：
        宫保鸡丁 | 辣炒鸡丁配花生 | 15 | 2
        麻婆豆腐 | 川式香辣豆腐 | 12 | 2
        干煸四季豆 | 爆炒四季豆 | 10 | 1

        错误示例：
        Kung Pao Chicken | 宫保鸡丁 | 15 | 2  （菜名未翻译）
        宫保鸡丁：辣子鸡 | 配花生 | 15元 | 2类  （格式错误）

        需要翻译的内容：
        """ + menu_text
        
        # 调用翻译API
        translate_response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的中餐菜单翻译助手。你必须将所有内容（包括菜品名称）翻译成地道的中文，使用标准的中餐菜名。保持格式不变，不添加任何额外内容。"
                },
                {
                    "role": "user",
                    "content": translate_prompt
                }
            ],
            max_tokens=4096,
            temperature=0.3
        )
        
        # 处理翻译结果
        translated_text = translate_response.choices[0].message.content.strip()
        translated_items = translated_text.split('\n')
        
        # 构建最终的分类结果
        final_categories = {
            "1": {
                "name": "前菜/凉菜",
                "items": []
            },
            "2": {
                "name": "主菜/热菜",
                "items": []
            },
            "3": {
                "name": "汤类",
                "items": []
            },
            "4": {
                "name": "主食/面食",
                "items": []
            },
            "5": {
                "name": "甜点",
                "items": []
            },
            "6": {
                "name": "饮品",
                "items": []
            },
            "7": {
                "name": "其他",
                "items": []
            }
        }
        
        # 处理翻译后的结果
        for item in translated_items:
            try:
                parts = item.split(" | ")
                if len(parts) == 4:  # 确保格式正确
                    name, desc, price, category = parts
                    # 获取对应的原始英文菜名
                    original_parts = menu_text.split('\n')[translated_items.index(item)].split(" | ")
                    original_name = original_parts[0] if len(original_parts) >= 1 else "Unknown"
                    
                    # 清理category字符串，只保留数字
                    category = ''.join(filter(str.isdigit, category))
                    # 确保category在有效范围内
                    if category in final_categories:
                        final_categories[category]["items"].append({
                            "name": name,
                            "original_name": original_name,  # 添加原始英文名称
                            "description": desc,
                            "price": price,
                            "category": category
                        })
                    else:
                        print(f"Warning: Invalid category '{category}' for translated item '{name}'")
            except Exception as item_error:
                print(f"Warning: Error processing translated item '{item}': {str(item_error)}")
                continue
        
        # 构建返回数据
        menu_analysis = {
            "categories": final_categories,
            "processing_time": f"{time.time() - start_time:.2f}",
            "timestamp": datetime.now().strftime('%d/%b/%Y %H:%M:%S'),
            "raw_text": menu_text,  # 原始英文文本
            "translated_text": translated_text,  # 翻译后的中文文本
            "total_items": len(menu_items)
        }
        
        print("\n=== Translation Result ===")
        print(f"Translated text:\n{translated_text}")
        print("\n=== Final Categories ===")
        for cat_id, cat_data in final_categories.items():
            print(f"\n{cat_data['name']} (Category {cat_id}):")
            for item in cat_data['items']:
                print(f"- {item['name']} | {item['description']} | {item['price']}")
        
        return make_succ_response(menu_analysis)
        
    except Exception as e:
        import traceback
        error_message = str(e)
        print("\n=== Error Details ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {error_message}")
        print("Stack trace:")
        print(traceback.format_exc())
        return make_err_response({
            "error": f"菜单分析失败: {error_message}",
            "timestamp": datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        })


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口,返回服务状态
    :return: 返回服务状态信息
    """
    try:
        # 检查数据库连接
        db.session.execute('SELECT 1')
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 构建状态信息
    status = {
        "status": "running",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "service": "flask-menu-analyzer",
        "database": db_status,
        "version": "1.0.0"  # 可以根据需要设置版本号
    }
    
    return make_succ_response(status)
