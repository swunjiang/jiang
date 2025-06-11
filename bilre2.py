import requests
import json
import time
import re
import csv
from datetime import datetime
import os

def get_video_info(bvid):
    """获取视频信息（包含oid）"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 0:
            return data['data']['aid'], data['data']['title']
        raise Exception(f"API错误: {data.get('message')}")
    except Exception as e:
        print(f"获取视频信息失败: {str(e)}")
        return None, None

def get_comments(oid, page=1):
    """获取单页评论 - 使用新版API"""
    url = "https://api.bilibili.com/x/v2/reply/wbi/main"
    params = {
        "next": page,
        "type": 1,
        "oid": oid,
        "mode": 3,  # 排序模式: 3-最新, 2-最热
        "plat": 1,
        "web_location": 1315875,
        "wts": int(time.time())
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/BV1xx411c7BF",
        "Origin": "https://www.bilibili.com"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取评论失败(第{page}页): {str(e)}")
        return None

def safe_get(data, keys, default=None):
    """安全获取嵌套字典值"""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data

def parse_comments(comment_data):
    """解析评论数据 - 增强健壮性"""
    comments = []
    try:
        # 处理一级评论
        replies = safe_get(comment_data, ['data', 'replies']) or []
        
        for reply in replies:
            try:
                # 使用安全获取方法处理可能缺失的字段
                user_name = safe_get(reply, ['member', 'uname'], '未知用户')
                content = safe_get(reply, ['content', 'message'], '')
                ctime = safe_get(reply, ['ctime'], int(time.time()))
                like_count = safe_get(reply, ['like'], 0)
                
                comments.append({
                    "user": user_name,
                    "content": content,
                    "time": datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S"),
                    "like": like_count,
                    "level": 1
                })
                
                # 处理二级评论（楼中楼）
                sub_replies = safe_get(reply, ['replies']) or []
                for sub_reply in sub_replies:
                    try:
                        sub_user = safe_get(sub_reply, ['member', 'uname'], '未知用户')
                        sub_content = safe_get(sub_reply, ['content', 'message'], '')
                        sub_ctime = safe_get(sub_reply, ['ctime'], int(time.time()))
                        sub_like = safe_get(sub_reply, ['like'], 0)
                        
                        comments.append({
                            "user": sub_user,
                            "content": sub_content,
                            "time": datetime.fromtimestamp(sub_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                            "like": sub_like,
                            "level": 2
                        })
                    except Exception as e:
                        print(f"解析二级评论时出错: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"解析一级评论时出错: {str(e)}")
                continue
        
        # 处理置顶评论 - 使用更安全的方法
        top_data = safe_get(comment_data, ['data', 'top', 'reply'])
        if top_data:
            try:
                top_user = safe_get(top_data, ['member', 'uname'], '未知用户')
                top_content = safe_get(top_data, ['content', 'message'], '')
                top_ctime = safe_get(top_data, ['ctime'], int(time.time()))
                top_like = safe_get(top_data, ['like'], 0)
                
                comments.insert(0, {
                    "user": top_user,
                    "content": "[置顶] " + top_content,
                    "time": datetime.fromtimestamp(top_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                    "like": top_like,
                    "level": 0
                })
            except Exception as e:
                print(f"解析置顶评论时出错: {str(e)}")
                
        return comments
    except Exception as e:
        print(f"解析评论数据时出错: {str(e)}")
        return comments

def save_comments(comments, filename="bilibili_comments.csv"):
    """保存评论到CSV文件 - 修复路径问题"""
    try:
        # 如果文件名包含路径，确保目录存在
        if os.path.dirname(filename) and not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["用户", "评论内容", "时间", "点赞数", "评论层级"])
            
            for comment in comments:
                # 清理内容中的换行符
                clean_content = comment['content'].replace('\n', ' ').replace('\r', '')
                writer.writerow([
                    comment['user'],
                    clean_content,
                    comment['time'],
                    comment['like'],
                    comment['level']
                ])
                
        print(f"评论已保存到: {filename}")
        return True
    except Exception as e:
        print(f"保存文件失败: {str(e)}")
        return False

def main():
    print("=" * 50)
    print("B站(Bilibili)视频评论下载工具 v2.1")
    print("=" * 50)
    
    # 获取用户输入
    video_url = input("请输入B站视频链接: ").strip()
    
    # 从URL中提取BV号
    bvid_match = re.search(r"(BV[0-9A-Za-z]{10})", video_url)
    if not bvid_match:
        print("错误: 无法从URL中提取BV号，请确认链接格式正确")
        return
    
    bvid = bvid_match.group(0)
    print(f"提取到视频BV号: {bvid}")
    
    # 获取视频信息
    oid, title = get_video_info(bvid)
    if not oid:
        print("获取视频信息失败，程序终止")
        return
    
    print(f"视频标题: {title}")
    print(f"视频OID: {oid}")
    
    # 获取评论
    all_comments = []
    page = 1
    max_retries = 3
    max_pages = 50
    comment_count = 0
    
    print("开始获取评论...")
    
    while page <= max_pages:
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            print(f"获取第 {page} 页评论...", end="", flush=True)
            data = get_comments(oid, page)
            
            if not data:
                print(" [无响应]")
                retry_count += 1
                time.sleep(2)
                continue
            
            if data.get('code') != 0:
                print(f" [失败: {data.get('message')}]")
                retry_count += 1
                time.sleep(2)
                continue
            
            comments = parse_comments(data)
            if comments:
                all_comments.extend(comments)
                new_count = len(comments)
                comment_count += new_count
                print(f" [成功获取 {new_count} 条评论]")
                success = True
            else:
                print(" [无评论数据]")
                success = True
        
        if not success:
            print(f" [连续 {max_retries} 次获取失败，跳过第 {page} 页]")
        
        # 检查是否还有更多评论
        if data and data.get('data', {}).get('cursor', {}).get('is_end', True):
            print("已到达最后一页评论")
            break
        
        page += 1
        time.sleep(1.2)  # 防止请求过快
    
    # 保存结果 - 修复路径问题
    if all_comments:
        # 创建保存目录（如果不存在）
        output_dir = "bilibili_comments"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建输出目录: {output_dir}")
        
        # 生成安全的文件名
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]  # 移除非法字符并截断
        filename = os.path.join(output_dir, f"{bvid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_comments.csv")
        
        if save_comments(all_comments, filename):
            print(f"共获取 {comment_count} 条评论")
            print(f"结果文件: {os.path.abspath(filename)}")
        else:
            print("评论获取成功但保存失败")
    else:
        print("未获取到任何评论")
    
    # 添加暂停以便查看结果
    input("\n按 Enter 键退出...")

if __name__ == "__main__":
    main()