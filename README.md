# 简简的表情包 MCP · jian-stickers

这是一个只读、无须上传密钥的个人表情包 MCP。图库仍位于本公开仓库，语义标签在 `stickers.json` 中维护。

**已有图片不必重传或重命名。** 当前索引包含 `39.jpeg`—`64.jpeg` 共 26 张，均带 `caption`、`tags` 和 `verified` 字段。数字文件名由清单提供语义映射。

## 两个工具

- `list_stickers()`：读取索引，列出可用表情包及语义标签。
- `show_sticker(filename)`：确保该图片经清单验证，从 jsDelivr 优先读取（失败时回退 GitHub Raw），返回 MCP `ImageContent` 真实图片数据，而非只返回 URL。

**重要限制：** MCP 服务器可以将图片数据提供给模型，但 ChatGPT 是否将该工具结果作为对话消息中的可见图片展示，取决于使用该插件的具体界面。安装完成后必须实际试发验证，不能仅凭代码保证在普通 Chat 里出现内联图片。

## 部署至 Render（网页操作）

1. 把本压缩包中 `sticker_mcp.py`、`requirements.txt`、`render.yaml`、`README.md` 四个文件添加到 GitHub 仓库根目录。覆盖已有 `sticker_mcp.py` 和 `README.md`，**不要删除** `stickers.json` 或图片。
2. 在 Render 创建 Web Service，关联仓库 `1106540310wen-sketch/jian-stickers` 的 `main` 分支。可使用仓库里的 `render.yaml` 作为 Blueprint，或者手动配置：Python / build `pip install -r requirements.txt` / start `python sticker_mcp.py`。
3. 环境变量设置 `MCP_TRANSPORT=streamable-http`。服务会监听 Render 提供的 `PORT`。
4. 部署成功后记下服务 HTTPS 域名。MCP 地址为 `https://<你的域名>/mcp`，**不是** GitHub 地址，也不是 jsDelivr 图片地址。

免费实例可能休眠，首次调用可能等待较久。公众可访问这个不需要认证的只读服务；若之后扩展私人数据或写操作，必须先增加鉴权。

## 在 ChatGPT 连接

在 ChatGPT 的 Plugins 页面点 `+` → `Add custom MCP server`，输入名称（如 `简简表情包`）、HTTPS 的 `/mcp` 地址、认证（本示例为 `No authentication`），阅读风险提示并确认后创建。安装后在 ChatGPT **Work** 中用 `@简简表情包` 调用测试；具体功能入口与账户、工作区权限有关。

测试：

1. `@简简表情包 调用 list_stickers，告诉我有多少张`。
2. `@简简表情包 调用 show_sticker，传入 58.jpeg，给我看真正的图片`。
3. 检查图片是否直接出现在聊天消息里；如果只有工具预览或文本，说明客户端展示端仍有限制，不能把“获取图片成功”等同于“图片已经发给用户”。

## 自然调用约定

> 平常闲聊时，可根据语境主动选择合适的表情包；不要每次征求同意。先用 `list_stickers` 看含义，选一张调用 `show_sticker`。不必每句话发送，不要重复刷屏；优先返回图片内容，不要用图片链接冒充已发送的图片。

## 本地测试

```bash
python -m pip install -r requirements.txt
python sticker_mcp.py  # 默认为 stdio，供本地 MCP 客户端使用
```

Web 服务本地启动：

```bash
MCP_TRANSPORT=streamable-http PORT=10000 python sticker_mcp.py
# 本地 MCP endpoint: http://localhost:10000/mcp
```

该仓库示例针对目前的 `mcp` Python SDK 2.x，工具返回 `Image` 并由 SDK 自动序列化为图片数据；实际聊天内的显示行为仍取决于客户端。
