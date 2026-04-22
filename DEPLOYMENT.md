# 📝 部署指南

本指南将帮助您完成从 GitHub 到 Hugging Face Space 的完整部署流程。

## ✅ 已完成

- [x] 创建 GitHub 仓库：`netease-music-24h`
- [x] 添加主程序 `app.py`
- [x] 添加依赖文件 `requirements.txt`
- [x] 添加部署脚本 `deploy.py`
- [x] 配置 GitHub Actions 工作流
- [x] 创建完整文档

## 🔧 需要手动完成的步骤

### 步骤 1：在 Hugging Face 创建 Space

1. 访问 https://huggingface.co/spaces
2. 点击 **"Create new space"**
3. 填写以下信息：
   - **Space name**: `netease-music-24h` (或其他你喜欢的名字)
   - **License**: MIT
   - **Space SDK**: Gradio
   - **Visibility**: Public 或 Private（根据需要选择）
4. 点击 **"Create Space"**

### 步骤 2：获取 Hugging Face Token

1. 访问 https://huggingface.co/settings/tokens
2. 点击 **"New token"**
3. 填写名称（如：github-actions）
4. 权限选择：**Write**
5. 点击 **"Generate token"**
6. **重要**：复制生成的 token，稍后使用

### 步骤 3：在 GitHub 配置 Secrets

1. 打开您的 GitHub 仓库：https://github.com/wang1520166813/netease-music-24h
2. 进入 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **"New repository secret"**
4. 添加以下 Secrets：

| Name | Value |
|------|-------|
| `HF_TOKEN` | 步骤 2 中获取的 Hugging Face token |
| `HF_SPACE_NAME` | 您的 Space 名称（格式：`wang1520166813/netease-music-24h`） |

5. 点击 **"Add secret"** 保存

### 步骤 4：触发自动部署

1. 确保代码已推送到 main 分支（已完成）
2. GitHub Actions 会自动触发部署
3. 查看 Actions 标签页确认部署状态：https://github.com/wang1520166813/netease-music-24h/actions

### 步骤 5：在 Hugging Face Space 配置环境变量

1. 打开您的 Hugging Face Space 页面
2. 点击右上角的 **"Settings"**
3. 找到 **"Repository secrets"** 部分
4. 添加以下环境变量：

| Key | Value |
|-----|-------|
| `MUSIC_U` | 您的网易云音乐 MUSIC_U Cookie |
| `PLAYLIST_ID` | 要播放的歌单 ID（如：1959142287） |

5. 保存后 Space 会自动重启

### 步骤 6：使用应用

1. 等待 Space 部署完成（大约 2-5 分钟）
2. 打开 Space 页面
3. 在控制面板输入：
   - **MUSIC_U Cookie**: 您的网易云音乐 Cookie
   - **歌单 ID**: 要播放的歌单 ID
4. 点击 **"开始播放"**

## 📋 获取 MUSIC_U Cookie 详细步骤

1. 打开浏览器（推荐使用 Chrome 或 Edge）
2. 访问 https://music.163.com
3. 登录您的网易云音乐账号
4. 按 `F12` 打开开发者工具
5. 切换到 **Network**（网络）标签页
6. 刷新页面（F5）
7. 在左侧请求列表中点击任意请求
8. 在右侧 **Headers** 标签页找到 **Cookie** 部分
9. 复制 `MUSIC_U` 的值（一长串字符）

**示例**：
```
MUSIC_U=0A5C4E8B9D2F1A3E7B6C9D8E5F2A1B4C7D0E3F6A9B2C5D8E1F4A7B0C3D6E9F2
```

## 🎯 获取歌单 ID 详细步骤

1. 打开网易云音乐网页版
2. 进入任意歌单页面
3. 查看浏览器地址栏 URL
4. 复制 `id=` 后面的数字

**示例 URL**：
```
https://music.163.com/#/playlist?id=1959142287
```
**歌单 ID**：`1959142287`

## 🔍 验证部署

### 检查 GitHub Actions 状态

访问：https://github.com/wang1520166813/netease-music-24h/actions

- ✅ 绿色对勾表示部署成功
- ⏳ 黄色时钟表示正在部署
- ❌ 红色叉号表示部署失败（点击查看详情）

### 检查 Hugging Face Space

访问：https://huggingface.co/spaces/wang1520166813/netease-music-24h

- 页面加载成功表示应用运行正常
- 可以看到 Gradio 控制面板

## 🐛 故障排除

### 部署失败

**问题**：GitHub Actions 显示失败

**解决方法**：
1. 检查 Secrets 是否正确配置
2. 确认 HF_TOKEN 权限足够（需要 Write 权限）
3. 确认 Space 名称格式正确（username/space-name）
4. 查看 Actions 日志了解详细错误

### Space 无法启动

**问题**：Hugging Face Space 一直显示 Building 或 Error

**解决方法**：
1. 检查 Space 配置是否为 Gradio
2. 确认 `requirements.txt` 存在
3. 查看 Space 的 Logs 标签页
4. 尝试重启 Space（Settings → Factory reboot）

### 登录失败

**问题**：应用提示登录失败

**解决方法**：
1. 确认 MUSIC_U Cookie 未过期
2. 重新获取 MUSIC_U（有效期约 30 天）
3. 检查网络连接

### 无法播放歌曲

**问题**：播放歌曲时报错

**解决方法**：
1. 确认歌单 ID 正确
2. 检查歌单是否为公开歌单
3. 查看日志了解具体错误
4. 尝试更换其他歌单

## 📞 其他说明

### 安全提醒

- ⚠️ **不要分享**您的 MUSIC_U Cookie 给他人
- ⚠️ **不要泄露**Hugging Face Token
- ⚠️ 定期更换 Token 和 Cookie
- ✅ 所有敏感信息都已通过环境变量管理

### 自动更新

- 推送代码到 main 分支会自动部署
- 修改 `app.py` 或 `requirements.txt` 会触发重新部署
- 可以在 GitHub Actions 中查看部署历史

### 性能优化

- 建议使用 Private Space 保护隐私
- 长时间运行请注意资源使用
- 可在 Settings 中配置 Space 的休眠策略

## 📚 相关文件

- `app.py` - 主程序
- `requirements.txt` - Python 依赖
- `deploy.py` - 部署脚本
- `.github/workflows/deploy-to-hf.yml` - GitHub Actions 配置
- `README.md` - 项目说明
- `README_HF.md` - Hugging Face Space 说明

## 🎉 完成！

完成以上步骤后，您的网易云音乐挂机脚本就已经运行在 Hugging Face Space 上了！

享受音乐吧！🎵
