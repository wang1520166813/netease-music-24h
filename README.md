# 🎵 网易云音乐 24 小时挂机脚本

一个基于 Gradio 的网易云音乐自动挂机工具，支持 24 小时循环播放、自动切歌、异常重连功能，并提供 Web 控制面板。

## ✨ 功能特性

- 🔐 **安全登录**: 使用 MUSIC_U Cookie 登录，无需账号密码
- 🔄 **循环播放**: 自动循环播放指定歌单
- 🎶 **自动切歌**: 模拟真实听歌行为，随机等待 3-5 分钟
- 🔌 **异常重连**: 网络异常自动重连
- 📊 **实时监控**: Gradio 控制面板显示播放状态和日志
- 🚀 **自动部署**: 代码推送自动部署到 Hugging Face Space
- 🔒 **安全认证**: 使用 GitHub Secrets 存储敏感信息

## 📋 前置要求

1. **网易云音乐账号**: 需要有效的 MUSIC_U Cookie
2. **Hugging Face 账号**: 用于创建 Space
3. **GitHub 账号**: 用于代码托管和 Actions

## 🚀 快速开始

### 1. 获取 MUSIC_U Cookie

1. 打开网易云音乐网页版 (https://music.163.com)
2. 登录您的账号
3. 按 F12 打开开发者工具
4. 进入 Network 标签页，刷新页面
5. 找到任意请求，查看 Cookie 中的 `MUSIC_U` 值

### 2. 创建 Hugging Face Space

1. 访问 https://huggingface.co/spaces
2. 点击 "Create new space"
3. 填写信息：
   - **Space name**: `netease-music-24h`
   - **License**: MIT
   - **Space SDK**: Gradio
   - **Visibility**: Public 或 Private

### 3. 配置 GitHub Secrets

在 GitHub 仓库设置中添加 Secrets：

1. 进入仓库 Settings → Secrets and variables → Actions
2. 添加以下 Secrets：

```
HF_TOKEN: 你的 Hugging Face Token
HF_SPACE_NAME: 你的 Space 名称 (格式：username/space-name)
```

**获取 HF_TOKEN**:
- 访问 https://huggingface.co/settings/tokens
- 创建新 Token，权限选择 `write`

### 4. 部署到 Hugging Face

代码推送到 main 分支后，GitHub Actions 会自动部署：

```bash
git add .
git commit -m "初始化项目"
git push origin main
```

## 📁 项目结构

```
netease-music-24h/
├── app.py                          # 主程序
├── requirements.txt                # Python 依赖
├── deploy.py                       # 部署脚本
├── .github/
│   └── workflows/
│       └── deploy-to-hf.yml       # GitHub Actions 工作流
└── README.md                       # 说明文档
```

## 🎮 使用方式

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export MUSIC_U="你的 MUSIC_U Cookie"
export PLAYLIST_ID="歌单 ID"

# 运行程序
python app.py
```

### Hugging Face Space

1. 在 Space 的 Settings 中设置环境变量：
   - `MUSIC_U`: 你的 MUSIC_U Cookie
   - `PLAYLIST_ID`: 要播放的歌单 ID

2. 重启 Space 后即可使用

## 🎯 获取歌单 ID

1. 打开网易云音乐网页版
2. 进入任意歌单
3. 复制 URL 中的数字部分

例如：`https://music.163.com/#/playlist?id=1959142287`
歌单 ID 为：`1959142287`

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| MUSIC_U | 网易云音乐 Cookie | 是 |
| PLAYLIST_ID | 歌单 ID | 是 |
| PORT | 服务端口 (默认 7860) | 否 |

### GitHub Secrets

| 变量名 | 说明 |
|--------|------|
| HF_TOKEN | Hugging Face 访问令牌 |
| HF_SPACE_NAME | Space 名称 (username/space-name) |

## 📊 控制面板功能

- **开始播放**: 启动挂机程序
- **停止播放**: 停止当前播放
- **刷新状态**: 更新播放状态
- **实时日志**: 查看播放日志和错误信息

## 🔧 故障排除

### 登录失败
- 检查 MUSIC_U Cookie 是否有效
- Cookie 可能过期，需要重新获取

### 播放失败
- 检查网络连接
- 确认歌单 ID 是否正确
- 查看日志了解具体错误

### 部署失败
- 检查 HF_TOKEN 是否正确
- 确认 Space 名称格式正确
- 查看 GitHub Actions 日志

## ⚠️ 注意事项

1. **账号安全**: 请妥善保管 MUSIC_U Cookie，不要泄露
2. **使用限制**: 合理使用挂机功能，避免被封禁
3. **网络要求**: 确保服务器可以访问网易云音乐
4. **资源占用**: 长时间运行请注意资源消耗

## 📝 更新日志

- **v1.0.0** (2026-04-23)
  - 初始版本发布
  - 支持 MUSIC_U 登录
  - Gradio 控制面板
  - 自动部署到 Hugging Face

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

感谢网易云音乐提供优质的音乐服务！
