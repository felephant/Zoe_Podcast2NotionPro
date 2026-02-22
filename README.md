## Obsidian 同步（新增）

可以在同步 Notion 的同时，自动把每条 Episode 生成 Markdown 到你的 Obsidian 目录。

在 `.env` 增加：

```env
OBSIDIAN_SYNC_ENABLED=true
OBSIDIAN_EXPORT_DIR=/你的/Obsidian/Vault/Podcast
```

如果你希望再自动上传到 Google Drive（例如 Obsidian Vault 在 Drive 中）：

```env
GOOGLE_DRIVE_FOLDER_ID=你的Drive文件夹ID
GOOGLE_OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
GOOGLE_OAUTH_CLIENT_ID=你的client_id
GOOGLE_OAUTH_CLIENT_SECRET=你的client_secret
GOOGLE_OAUTH_REFRESH_TOKEN=你的refresh_token
# 可选：GOOGLE_OAUTH_SCOPE=https://www.googleapis.com/auth/drive.file
```

- 现在支持自动刷新 Access Token，优先使用 `refresh_token` 流程
- 程序会在运行时更新本地 `.env` 里的 `GOOGLE_DRIVE_ACCESS_TOKEN`，用于后续运行复用
- `GOOGLE_DRIVE_FOLDER_ID` 是目标文件夹 ID（URL 中 `folders/<ID>` 的部分）

同步结果：
- 本地文件：`$OBSIDIAN_EXPORT_DIR/<播客名>/<EID>-<标题>.md`
- Drive：若同名文件已存在则覆盖更新，不存在则创建

## 使用

> [!IMPORTANT]  
> 关注公众号回复播客查看教程，后续有更新也会第一时间在公众号里同步。

![扫码_搜索联合传播样式-标准色版](https://github.com/malinkang/weread2notion/assets/3365208/191900c6-958e-4f9b-908d-a40a54889b5e)


## 群
> [!IMPORTANT]  
> 欢迎加入群讨论。可以讨论使用中遇到的任何问题，也可以讨论Notion使用，后续我也会在群中分享更多Notion自动化工具。微信群失效的话可以添加我的微信malinkang，我拉你入群。

| 微信群 | QQ群 |
| --- | --- |
| <div align="center"><img src="https://github.com/malinkang/weread2notion/assets/3365208/f230a01f-bc1a-48dc-95f6-ac7ad0d1ecc5" ></div> | <div align="center"><img src="https://images.malinkang.com/2024/04/b225b17d60670e4a6ff3459bbde80d28.jpg" width="50%"></div> |

## 捐赠

如果你觉得本项目帮助了你，请作者喝一杯咖啡，你的支持是作者最大的动力。本项目会持续更新。

| 支付宝支付 | 微信支付 |
| --- | --- |
| <div align="center"><img src="https://images.malinkang.com/2024/03/7fd0feb1145f19fab3821ff1d4631f85.jpg" width="50%"></div> | <div align="center"><img src="https://images.malinkang.com/2024/03/d34f577490a32d4440c8a22f57af41da.jpg" width="50%"></div> |

## 其他项目
* [WeRead2Notion-Pro](https://github.com/malinkang/weread2notion-pro)
* [WeRead2Notion](https://github.com/malinkang/weread2notion)
* [Podcast2Notion](https://github.com/malinkang/podcast2notion)
* [Douban2Notion](https://github.com/malinkang/douban2notion)
* [Keep2Notion](https://github.com/malinkang/keep2notion)
