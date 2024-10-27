import subprocess
import os
import requests

def process_subtitle_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in lines:
            line = line.strip()
            if line and not line[0].isdigit():  # 只写入字幕内容
                f.write(line + '\n')

def get_bilibili_video_info(url):
    # 指定字幕保存的目录
    save_dir = "./BBDown/data" 
    os.makedirs(save_dir, exist_ok=True) 

    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    command = [
        os.path.join(script_dir, 'BBDown', 'BBDown.exe'),  
        url,
        '--sub-only',
        '--skip-ai', 'false',
        '--work-dir', save_dir,
        '--file-pattern', 'temp'
    ]
    try:
        # 运行命令并获取输出
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout
        
        # 打印输出内容以便调试
        # print("完整输出内容:")
        print(output)
        
        # 解析输出以提取标题
        lines = output.splitlines()
        video_info = {}
        
        for line in lines:
            if "视频标题:" in line:
                video_info['title'] = line.split("视频标题:")[1].strip()
        
        # 检查字幕文件
        ai_subtitle_file = os.path.join(save_dir, 'temp.ai-zh.srt')
        zh_subtitle_file = os.path.join(save_dir, 'temp.zh-CN.srt')
        output_subtitle_file = os.path.join(save_dir, "temp_processed.srt")

        if ai_subtitle_file or zh_subtitle_file:
            if os.path.exists(ai_subtitle_file):
                if os.path.exists(output_subtitle_file):
                    os.remove(output_subtitle_file) 
                process_subtitle_file(ai_subtitle_file, output_subtitle_file)  
                video_info['subtitle_file'] = output_subtitle_file
                print(f"保留 AI 字幕: {output_subtitle_file}")
            elif os.path.exists(zh_subtitle_file):
                if os.path.exists(output_subtitle_file):
                    os.remove(output_subtitle_file)  
                process_subtitle_file(zh_subtitle_file, output_subtitle_file) 
                video_info['subtitle_file'] = output_subtitle_file
                print(f"保留 zh-CN 字幕: {output_subtitle_file}")
            else:
                video_info['subtitle_file'] = '未获取到字幕文件'   
            #删除临时字幕
            if os.path.exists(ai_subtitle_file):
                os.remove(ai_subtitle_file)
            if os.path.exists(zh_subtitle_file):
                os.remove(zh_subtitle_file)
        else:
            video_info['subtitle_file'] = '未获取到字幕文件'
            

        
        return video_info

    except Exception as e:
        print(f"错误: {e}")
        return None

def read_subtitle_file(subtitle_file_path):
    try:
        with open(subtitle_file_path, 'r', encoding='utf-8') as file:
            subtitle_content = file.read()
        return subtitle_content
    except FileNotFoundError:
        print(f"字幕文件未找到: {subtitle_file_path}")
        return None
    except Exception as e:
        print(f"读取字幕文件时出错: {e}")
        return None
    
def gpt_summary(message):
    url = "https://api.openai.com"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 你的apiKey" # 替换为你的API key
    }

    # 添加总结指示
    instruction = "请你重新分点总结以下所有内容，分段分点总结，给每段一个小标题(需要加数字),每段下最多不超过8点(需要加数字),没有字数限制,必须输出中文。"
    full_message = f"{instruction}\n{message}"

    data = {
        "model": "gpt-3.5-turbo-0125",
        "messages": [{"role": "user", "content": full_message}],
        "temperature": 0.7,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        content = response_json['choices'][0]['message']['content']
        return content
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}") 
        return "发送失败"
    
def bilibili_summary(url):
    try:
        video_info = get_bilibili_video_info(url)
        title = video_info.get('title', '未获取到标题')
        subtitle_file = video_info.get('subtitle_file')

        if subtitle_file and subtitle_file != '未获取到字幕文件':
            subtitle_content = read_subtitle_file(subtitle_file)

            if subtitle_content:
                summary = gpt_summary(subtitle_content)
                return f"视频标题: {title}\n总结: \n{summary}"
            else:
                return f"视频标题: {title}\n未读取到字幕,无法总结。"
        else:
            return f"视频标题: {title}\n未获取到字幕,无法总结。"
    except Exception as e:
        return f"发生异常: {str(e)}"

if __name__ == "__main__":
    print(bilibili_summary('https://www.bilibili.com/video/BV1vu411u7bM/')) # 测试用例
