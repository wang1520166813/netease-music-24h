#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐 24 小时挂机脚本
支持 MUSIC_U Cookie 登录、循环播放、自动切歌、异常重连
提供 Gradio 控制面板显示播放状态和日志

版本：v1.0.7
更新：全量读取歌单所有歌曲（支持 3500+ 首），分页获取
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
        self.skip_count = 0
        self.start_time = None
        self.logs: List[str] = []
        self.music_u = ""
        self.playlist_id = ""
        self.running = False
        self.last_stop_time = None
        self.manual_stop = False
        
    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(message)
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
        """获取歌单所有歌曲（分页读取）"""
        all_tracks = []
        page_size = 1000  # 每次请求 1000 首
        offset = 0
        total = 0
        
        try:
            state.add_log(f"🔄 开始分页获取歌单歌曲，歌单 ID: {playlist_id}")
            
            while True:
                url = f'https://music.163.com/api/v3/playlist/detail?id={playlist_id}&n={page_size}&offset={offset}'
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    state.add_log(f"获取歌单失败：状态码 {response.status_code}")
                    break
                
                data = response.json()
                
                if 'playlist' not in data or not data['playlist']:
                    break
                
                playlist_data = data['playlist']
                
                # 第一次请求时获取总数
                if total == 0:
                    total = playlist_data.get('trackCount', 0)
                    state.add_log(f"📊 歌单总歌曲数：{total}")
                
                tracks = playlist_data.get('tracks', [])
                if not tracks:
                    # 如果没有 tracks，尝试通过 trackIds 获取
                    track_ids = playlist_data.get('trackIds', [])
                    if track_ids:
                        # 获取所有歌曲 ID
                        all_song_ids = [t['id'] for t in track_ids]
                        # 分页获取歌曲详情
                        state.add_log(f"🔄 通过 trackIds 获取 {len(all_song_ids)} 首歌曲详情...")
                        return self._get_tracks_detail_paginated(all_song_ids)
                    break
                
                # 提取歌曲信息
                page_tracks = [{
                    'id': track['id'], 
                    'name': track['name'], 
                    'artist': track['ar'][0]['name'],
                    'fee': track.get('fee', 0)
                } for track in tracks]
                
                all_tracks.extend(page_tracks)
                state.add_log(f"📥 已获取 {len(all_tracks)}/{total} 首歌曲")
                
                # 如果已获取完所有歌曲，退出
                if len(all_tracks) >= total or len(tracks) < page_size:
                    break
                
                offset += page_size
                time.sleep(0.5)  # 避免请求过快
                
            state.add_log(f"✅ 歌单歌曲获取完成，共 {len(all_tracks)} 首")
            return all_tracks
            
        except Exception as e:
            state.add_log(f"获取歌单异常：{str(e)}")
            return all_tracks if all_tracks else []
    
    def _get_tracks_detail_paginated(self, track_ids: List[int]) -> List[dict]:
        """分页获取歌曲详情"""
        all_songs = []
        page_size = 100  # 每次请求 100 首
        
        try:
            for i in range(0, len(track_ids), page_size):
                batch_ids = track_ids[i:i+page_size]
                ids_str = ','.join(str(id) for id in batch_ids)
                url = f'https://music.163.com/api/song/detail?ids=[{ids_str}]'
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    songs = data.get('songs', [])
                    batch_songs = [{
                        'id': song['id'], 
                        'name': song['name'], 
                        'artist': song['artists'][0]['name'],
                        'fee': song.get('fee', 0)
                    } for song in songs]
                    all_songs.extend(batch_songs)
                    state.add_log(f"📥 已获取 {len(all_songs)}/{len(track_ids)} 首歌曲详情")
                time.sleep(0.3)  # 避免请求过快
                
            return all_songs
        except Exception as e:
            state.add_log(f"获取歌曲详情异常：{str(e)}")
            return all_songs
    
    def play_song(self, song_id: int) -> bool:
        try:
            url = f'https://music.163.com/api/song/enhance/player/url?id={song_id}&ids=[{song_id}]&br=320000'
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    if data['data'][0].get('url'):
                        return True
            return False
        except Exception as e:
            state.add_log(f"播放歌曲请求失败：{str(e)}")
            return False
    
    def update_play_count(self, song_id: int):
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
    state.running = True
    state.manual_stop = False
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
    
    # 过滤掉 VIP/版权受限歌曲 (fee != 0)
    free_playlist = [song for song in playlist if song.get('fee', 0) == 0]
    skipped_vip = len(playlist) - len(free_playlist)
    
    if skipped_vip > 0:
        state.add_log(f"⚠️ 检测到 {skipped_vip} 首 VIP/受限歌曲，已自动过滤，仅播放 {len(free_playlist)} 首免费歌曲")
    else:
        state.add_log(f"✅ 歌单中所有歌曲均可播放，共 {len(free_playlist)} 首")
    
    state.playlist = free_playlist
    state.add_log(f"获取到 {len(free_playlist)} 首可播放歌曲 🎵")
    
    state.is_playing = True
    state.play_count = 0
    state.error_count = 0
    state.skip_count = 0
    
    # 循环播放
    while state.running:
        for song in state.playlist:
            if not state.running:
                break
                
            state.current_song = f"{song['name']} - {song['artist']}"
            state.add_log(f"正在播放：{state.current_song}")
            
            # 尝试播放
            if player.play_song(song['id']):
                state.play_count += 1
                player.update_play_count(song['id'])
                state.add_log(f"播放成功，总播放数：{state.play_count}")
                
                # 正常等待 (3-5 分钟)
                wait_time = random.randint(180, 300)
                state.add_log(f"✅ 播放成功，等待 {wait_time} 秒后切换下一首")
                
                for _ in range(wait_time):
                    if not state.running:
                        break
                    time.sleep(1)
            else:
                # 播放失败（可能是临时网络问题或版权检查）
                state.error_count += 1
                state.add_log(f"❌ 播放失败（可能是网络波动或版权限制），立即跳过下一首！")
                continue
        
        # 如果歌单播完，重新循环
        state.add_log("🔄 歌单播放完毕，重新开始循环...")

    # 播放循环结束
    state.is_playing = False
    state.last_stop_time = datetime.now()
    
    if state.manual_stop:
        state.add_log("=== 挂机已手动停止 ===")
    else:
        state.add_log("=== 挂机意外停止，守护线程将在 1 分钟后尝试重启 ===")
    
    return "挂机已停止"

def stop_playing():
    state.manual_stop = True
    state.running = False
    state.add_log("用户请求停止播放")
    return "正在停止..."

def get_status():
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
- **跳过次数**: {state.skip_count}
- **错误次数**: {state.error_count}
- **运行时长**: {uptime}
- **状态**: {'🔴 运行中' if state.is_playing else '⚪ 已停止'}
- **可播放歌曲数**: {len(state.playlist)}
"""

def get_logs():
    return "\n".join(state.logs[-50:])

# 守护线程逻辑
def watchdog():
    while True:
        time.sleep(60)
        if not state.is_playing:
            if state.manual_stop:
                continue
            if state.last_stop_time:
                time_since_stop = (datetime.now() - state.last_stop_time).total_seconds()
                if time_since_stop < 60:
                    continue
            state.add_log("⚠️ 检测到挂机意外停止，守护线程正在尝试自动重启...")
            music_u = get_music_u()
            playlist_id = get_playlist_id()
            if music_u and playlist_id:
                state.add_log(f"🔄 使用默认配置自动重启：歌单 ID {playlist_id}")
                thread = threading.Thread(target=start_playing, args=(music_u, playlist_id))
                thread.daemon = True
                thread.start()
            else:
                state.add_log("❌ 自动重启失败：未找到默认配置")

# 启动守护线程
watchdog_thread = threading.Thread(target=watchdog, daemon=True)
watchdog_thread.start()

# Gradio 界面
def create_ui():
    default_music_u = os.getenv('MUSIC_U', '')
    default_playlist_id = os.getenv('PLAYLIST_ID', '1959142287')
    
    with gr.Blocks(title="网易云音乐挂机") as app:
        gr.Markdown("# 🎵 网易云音乐 24 小时挂机")
        gr.Markdown("> 支持循环播放、自动切歌、异常重连 | 版本：v1.0.7 (全量读取 3500+ 首)")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 控制面板")
                
                music_u_input = gr.Textbox(
                    label="MUSIC_U Cookie",
                    placeholder="请输入您的 MUSIC_U Cookie",
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
        
        def on_start(music_u, playlist_id):
            if not music_u:
                music_u = default_music_u
            if not playlist_id:
                playlist_id = default_playlist_id
            
            if not music_u:
                return "请先输入 MUSIC_U Cookie", get_status(), get_logs()
            if not playlist_id:
                return "请先输入歌单 ID", get_status(), get_logs()
            
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
    music_u = os.getenv('MUSIC_U', '')
    playlist_id = os.getenv('PLAYLIST_ID', '1959142287')
    
    app = create_ui()
    app.launch(
        server_name='0.0.0.0',
        server_port=int(os.getenv('PORT', 7860)),
        share=False,
        theme=gr.themes.Soft()
    )
