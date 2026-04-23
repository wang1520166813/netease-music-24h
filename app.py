#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐 24 小时挂机脚本
支持 MUSIC_U Cookie 登录、循环播放、自动切歌、异常重连
提供 Gradio 控制面板显示播放状态和日志

版本：v1.0.5
更新：增加守护线程，每分钟自动检测状态，意外停止自动重启
"""

import os
import time
import random
import logging
import threading
from datetime import datetime
from typing import Optional, List
import requests
import gradio as gr

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局状态
class PlayerState:
    def __init__(self):
        self.is_playing = False
        self.current_song = ""
        self.playlist = []
        self.play_count = 0
        self.error_count = 0
        self.start_time = None
        self.logs: List[str] = []
        self.music_u = ""
        self.playlist_id = ""
        self.running = False
        self.last_stop_time = None  # 记录上次停止的时间
        self.manual_stop = False    # 标记是否为用户手动停止
        
    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(message)
        # 保留最近 100 条日志
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

state = PlayerState()

class NetEaseMusic:
    """网易云音乐播放器类"""
    
    def __init__(self, music_u: str):
        self.music_u = music_u
        self.session = requests.Session()
        self.session.cookies.update({
            'MUSIC_U': music_u,
            'os': 'pc',
            'appver': '2.7.1'
        })
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://music.163.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.headers)
        
    def check_login(self) -> bool:
        """检查登录状态"""
        try:
            response = self.session.get(
                'https://music.163.com/api/nuser/account/get',
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            state.add_log(f"登录检查失败：{str(e)}")
            return False
    
    def get_playlist(self, playlist_id: str) -> List[dict]:
        """获取歌单歌曲列表"""
        try:
            url = f'https://music.163.com/api/v3/playlist/detail?id={playlist_id}&n=1000'
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'playlist' in data and data['playlist']:
                    tracks = data['playlist'].get('tracks', [])
                    if tracks:
                        return [{'id': track['id'], 'name': track['name'], 'artist': track['ar'][0]['name']} for track in tracks]
                    
                    track_ids = data['playlist'].get('trackIds', [])
                    if track_ids:
                        return self._get_tracks_detail([t['id'] for t in track_ids[:100]])
                
                if 'result' in data:
                    tracks = data['result'].get('tracks', [])
                    if tracks:
                        return [{'id': track['id'], 'name': track['name'], 'artist': track['artists'][0]['name']} for track in tracks]
            
            state.add_log(f"获取歌单失败：状态码 {response.status_code}")
            return []
            
        except Exception as e:
            state.add_log(f"获取歌单异常：{str(e)}")
            return []
    
    def _get_tracks_detail(self, track_ids: List[int]) -> List[dict]:
        """获取歌曲详情"""
        try:
            if not track_ids:
                return []
            
            ids_str = ','.join(str(id) for id in track_ids)
            url = f'https://music.163.com/api/song/detail?ids=[{ids_str}]'
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                songs = data.get('songs', [])
                return [{'id': song['id'], 'name': song['name'], 'artist': song['artists'][0]['name']} for song in songs]
        except Exception as e:
            state.add_log(f"获取歌曲详情失败：{str(e)}")
        
        return []
    
    def play_song(self, song_id: int) -> bool:
        """播放歌曲"""
        try:
            url = f'https://music.163.com/api/song/enhance/player/url?id={song_id}&ids=[{song_id}]&br=320000'
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            state.add_log(f"播放歌曲失败：{str(e)}")
            return False
    
    def update_play_count(self, song_id: int):
        """更新播放计数"""
        try:
            url = 'https://music.163.com/api/feedback/weblog'
            data = {
                'logs': f'[{{"action":"play","json":{{"sourceId":"{song_id}","time":"180","end":"play","source":"playlist"}}}}]'
            }
            self.session.post(url, data=data, timeout=5)
        except Exception as e:
            pass

def get_music_u() -> str:
    return os.getenv('MUSIC_U', '')

def get_playlist_id() -> str:
    return os.getenv('PLAYLIST_ID', '')

def start_playing(music_u: str, playlist_id: str):
    """开始播放流程"""
    state.running = True
    state.manual_stop = False  # 重置手动停止标志
    state.start_time = datetime.now()
    state.music_u = music_u
    state.playlist_id = playlist_id
    
    state.add_log("=== 网易云音乐挂机开始 ===")
    state.add_log(f"使用歌单 ID: {playlist_id}")
    
    player = NetEaseMusic(music_u)
    
    if not player.check_login():
        state.add_log("登录失败，请检查 MUSIC_U Cookie")
        state.running = False
        state.is_playing = False
        state.last_stop_time = datetime.now()
        return "登录失败，请检查 MUSIC_U Cookie"
    
    state.add_log("登录成功 ✅")
    
    playlist = player.get_playlist(playlist_id)
    if not playlist:
        state.add_log("获取歌单失败，请检查歌单 ID 是否正确或歌单是否为公开")
        state.running = False
        state.is_playing = False
        state.last_stop_time = datetime.now()
        return "获取歌单失败"
    
    state.playlist = playlist
    state.add_log(f"获取到 {len(playlist)} 首歌曲 🎵")
    
    state.is_playing = True
    state.play_count = 0
    state.error_count = 0
    
    # 循环播放
    while state.running:
        for song in playlist:
            if not state.running:
                break
                
            state.current_song = f"{song['name']} - {song['artist']}"
            state.add_log(f"正在播放：{state.current_song}")
            
            if player.play_song(song['id']):
                state.play_count += 1
                player.update_play_count(song['id'])
                state.add_log(f"播放成功，总播放数：{state.play_count}")
            else:
                state.error_count += 1
                state.add_log(f"播放失败，错误数：{state.error_count}")
            
            # 随机等待 (模拟听歌时间 3-5 分钟)
            wait_time = random.randint(180, 300)
            state.add_log(f"等待 {wait_time} 秒后切换下一首")
            
            for _ in range(wait_time):
                if not state.running:
                    break
                time.sleep(1)
    
    # 播放循环结束
    state.is_playing = False
    state.last_stop_time = datetime.now()
    
    # 如果是用户手动停止，记录日志
    if state.manual_stop:
        state.add_log("=== 挂机已手动停止 ===")
    else:
        state.add_log("=== 挂机意外停止，守护线程将在 1 分钟后尝试重启 ===")
    
    return "挂机已停止"

def stop_playing():
    """停止播放（用户手动）"""
    state.manual_stop = True
    state.running = False
    state.add_log("用户请求停止播放")
    return "正在停止..."

def get_status():
    """获取当前状态"""
    uptime = ""
    if state.start_time:
        delta = datetime.now() - state.start_time
        hours, minutes = divmod(delta.seconds // 60, 60)
        minutes = delta.seconds // 60 % 60
        uptime = f"{hours}小时{minutes}分钟"
    
    return f"""
### 播放状态
- **当前歌曲**: {state.current_song or '无'}
- **播放次数**: {state.play_count}
- **错误次数**: {state.error_count}
- **运行时长**: {uptime}
- **状态**: {'🔴 运行中' if state.is_playing else '⚪ 已停止'}
- **歌单歌曲数**: {len(state.playlist)}
"""

def get_logs():
    """获取日志"""
    return "\n".join(state.logs[-50:])

# --- 守护线程逻辑 ---
def watchdog():
    """
    守护线程：每分钟检查一次状态
    如果状态是“已停止”且不是用户手动停止，则自动重启
    """
    while True:
        time.sleep(60)  # 每分钟检查一次
        
        # 检查是否处于停止状态
        if not state.is_playing:
            # 检查是否是用户手动停止
            if state.manual_stop:
                # 用户手动停止，不重启
                continue
            
            # 检查距离上次停止是否超过 1 分钟 (防止刚停止就重启)
            if state.last_stop_time:
                time_since_stop = (datetime.now() - state.last_stop_time).total_seconds()
                if time_since_stop < 60:
                    continue
            
            # 如果是意外停止，且距离上次停止超过 1 分钟，则自动重启
            state.add_log("⚠️ 检测到挂机意外停止，守护线程正在尝试自动重启...")
            
            # 获取环境变量中的默认值
            music_u = get_music_u()
            playlist_id = get_playlist_id()
            
            if music_u and playlist_id:
                state.add_log(f"🔄 使用默认配置自动重启：歌单 ID {playlist_id}")
                # 启动新线程
                thread = threading.Thread(target=start_playing, args=(music_u, playlist_id))
                thread.daemon = True
                thread.start()
            else:
                state.add_log("❌ 自动重启失败：未找到默认配置 (MUSIC_U 或 PLAYLIST_ID)")

# 启动守护线程
watchdog_thread = threading.Thread(target=watchdog, daemon=True)
watchdog_thread.start()

# Gradio 界面
def create_ui():
    # 从环境变量获取默认值
    default_music_u = os.getenv('MUSIC_U', '')
    default_playlist_id = os.getenv('PLAYLIST_ID', '1959142287')
    
    with gr.Blocks(title="网易云音乐挂机") as app:
        gr.Markdown("# 🎵 网易云音乐 24 小时挂机")
        gr.Markdown("> 支持循环播放、自动切歌、异常重连 | 版本：v1.0.5 (带自动守护)")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 控制面板")
                
                music_u_input = gr.Textbox(
                    label="MUSIC_U Cookie",
                    placeholder="请输入您的 MUSIC_U Cookie（如已配置环境变量可留空）",
                    type="password",
                    value=default_music_u
                )
                playlist_id_input = gr.Textbox(
                    label="歌单 ID",
                    placeholder="请输入要播放的歌单 ID",
                    value=default_playlist_id
                )
                
                with gr.Row():
                    start_btn = gr.Button("🎵 开始播放", variant="primary")
                    stop_btn = gr.Button("⏹ 停止播放", variant="secondary")
                
                status_btn = gr.Button("🔄 刷新状态")
            
            with gr.Column(scale=1):
                gr.Markdown("### 状态信息")
                status_display = gr.Markdown(get_status())
        
        with gr.Row():
            logs_display = gr.Textbox(
                label="日志",
                lines=15,
                max_lines=50,
                interactive=False
            )
        
        # 事件处理
        def on_start(music_u, playlist_id):
            # 如果输入为空，使用环境变量默认值
            if not music_u:
                music_u = default_music_u
            if not playlist_id:
                playlist_id = default_playlist_id
            
            if not music_u:
                return "请先输入 MUSIC_U Cookie 或在环境变量中配置", get_status(), get_logs()
            if not playlist_id:
                return "请先输入歌单 ID 或在环境变量中配置", get_status(), get_logs()
            
            # 重置手动停止标志
            state.manual_stop = False
            
            import threading
            thread = threading.Thread(target=start_playing, args=(music_u, playlist_id))
            thread.daemon = True
            thread.start()
            
            time.sleep(2)
            return "挂机已启动", get_status(), get_logs()
        
        start_btn.click(
            fn=on_start,
            inputs=[music_u_input, playlist_id_input],
            outputs=[status_display, status_display, logs_display]
        )
        
        stop_btn.click(
            fn=stop_playing,
            outputs=[status_display]
        ).then(
            fn=get_status,
            outputs=[status_display]
        ).then(
            fn=get_logs,
            outputs=[logs_display]
        )
        
        status_btn.click(
            fn=get_status,
            outputs=[status_display]
        ).then(
            fn=get_logs,
            outputs=[logs_display]
        )
    
    return app

if __name__ == "__main__":
    # 从环境变量获取配置
    music_u = os.getenv('MUSIC_U', '')
    playlist_id = os.getenv('PLAYLIST_ID', '1959142287')
    
    # 创建并启动应用
    app = create_ui()
    app.launch(
        server_name='0.0.0.0',
        server_port=int(os.getenv('PORT', 7860)),
        share=False,
        theme=gr.themes.Soft()
    )
