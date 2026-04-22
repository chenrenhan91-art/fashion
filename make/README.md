# Draftelier · Make.com + Gemini 图像渲染接入

这份说明把前端（`index.html` + `assets/app.js`）与 Make.com webhook 连接起来，由 Make 代为调用 Google Gemini 的图像生成 API，**API Key 永远不会出现在前端代码里**。

---

## 一、架构

```
Browser (index.html)
  ├─ 上传图 + 选风格 + 点「生成 AI 渲染」
  └─ POST JSON → Make Webhook
                  ├─ HTTP 模块 → Gemini primary (gemini-3-pro-image-preview)
                  ├─ Router:  成功？ → 直接返回
                  │           失败？ → HTTP 模块 → Gemini fallback (gemini-2.5-flash-image)
                  └─ Webhook Response ← { ok, model, image_base64 }
Browser
  └─ 用返回的 base64 绘制到海报 Canvas（横 2000×1400 / 竖 1440×1800）
     + 品牌标 + 双语点评（Medium / Strokes / Vibe）+ 档案页脚
     + 下载 PNG + 分享（navigator.share / clipboard 回退）
```

---

## 二、在 Make.com 一键导入

1. 打开 <https://us2.make.com/1746591/scenarios/add>（已登录状态）。
2. 左上角 scenario 名称旁的 **•••** → **Import Blueprint**。
3. 选择文件：[make/draftelier-gemini-blueprint.json](make/draftelier-gemini-blueprint.json)。
4. 导入后会看到 3 个模块 + 1 个 Router：
   - `[1] Custom webhook`（入口）
   - `[2] HTTP – Gemini primary`
   - `Router` → 路线 A: `[4] Set variables` → `[5] Webhook Response`（成功）
   - Router → 路线 B: `[6] HTTP – Gemini fallback` → `[7] Webhook Response`（回退）

## 三、关键字段（必须手动改）

### Step A — 绑定 webhook
点 `[1] Custom webhook` → **Add** → 名称 `Draftelier` → **Save**。
复制生成的 URL，形如 `https://hook.us2.make.com/xxxxxxxxxxxxxx`。

### Step B — 填入 Gemini API Key（两处）
分别点 `[2] HTTP – Gemini primary` 和 `[6] HTTP – Gemini fallback`：
- 找到 `Headers` → `x-goog-api-key`
- 把值 `__REPLACE_WITH_YOUR_GEMINI_API_KEY__` 换成你从 <https://aistudio.google.com/app/apikey> 生成的 **真实** AI Studio key（`AIzaSy...`，39 字符）

> ⚠️ 你在聊天中贴出的 `AQ.Ab8RN6L6…` 看起来不是标准 AI Studio Key 格式（标准应以 `AIzaSy` 开头）。请重新生成一个，并把旧那串 Revoke。

### Step C — 打开 scenario
左下角开关从 OFF → ON。

### Step D — 把 webhook 地址交给前端
编辑 [assets/app.js](assets/app.js)，找到这一行：

```js
const MAKE_WEBHOOK_URL = window.DRAFTELIER_WEBHOOK || "";
```

改为：

```js
const MAKE_WEBHOOK_URL = window.DRAFTELIER_WEBHOOK || "https://hook.us2.make.com/你的hookid";
```

或者在 `index.html` 里 `<script src="assets/app.js">` 之前加：

```html
<script>window.DRAFTELIER_WEBHOOK = "https://hook.us2.make.com/你的hookid";</script>
```

---

## 四、前端行为

- 上传图 → 默认先用 **CSS lens**（本地滤镜）显示占位海报，零成本。
- 点击 **「生成 AI 渲染 ✦」** 才会真正调 Make webhook。
- 返回的 base64 图替换掉 CSS lens，继续合成海报。
- 海报右上角 3 个按钮：
  - `AUTO / 竖 / 横` —— 切海报长宽比
  - `下载 PNG ↓`
  - `分享 ↗`（优先走 `navigator.share({ files })`，失败回退剪贴板）

---

## 五、Webhook 的请求/返回契约

**请求 (前端 → Make)：**

```json
{
  "image_base64": "<不含 data:image/... 前缀的纯 base64>",
  "mime_type": "image/jpeg",
  "style_prompt": "Redraw this photograph in the visual language of \"Parisian Couture\" … ",
  "style_id": "dior",
  "style_token": "paris_new_look",
  "model": "gemini-3-pro-image-preview",
  "fallback_model": "gemini-2.5-flash-image",
  "aspect": "portrait"
}
```

**返回 (Make → 前端)：**

```json
{
  "ok": true,
  "model": "gemini-3-pro-image-preview",
  "image_base64": "<PNG base64>"
}
```

---

## 六、故障排查

| 现象 | 原因 | 修复 |
|---|---|---|
| 浏览器 Console: `Failed to fetch` | Make scenario 未打开 / webhook URL 拼错 | 检查 scenario 开关；校对 URL |
| Make 执行日志 HTTP 400 `API key not valid` | API key 还是占位符 / key 非 `AIzaSy` 格式 | 重新生成 AI Studio key 并替换两处 header |
| 返回 `image_base64` 为空 | 该模型对此输入拒绝生图（审核）或模型 ID 拼错 | 检查 `model` / `fallback_model` 字段；必要时降级 `gemini-2.5-flash-image` |
| 前端海报没有变化 | 未点"生成 AI 渲染 ✦"按钮 / 按钮灰色 | 按钮灰色说明 `MAKE_WEBHOOK_URL` 为空，按 Step D 配置 |
| 分享按钮报错 | 非 HTTPS 站点（GitHub Pages + CNAME 是 HTTPS，OK） | 确保站点用 HTTPS 打开，本地 `file://` 不支持 `navigator.share` |

---

## 七、安全提醒

- API Key 只放在 Make 的 HTTP 模块 header 里，不要提交到仓库。
- `make/draftelier-gemini-blueprint.json` 里是占位符 `__REPLACE_WITH_YOUR_GEMINI_API_KEY__`，可安全提交。
- 建议在 Google Cloud Console 为该 key 设置 **API restriction → Generative Language API only** 和 **Application restriction → HTTP referrers** 或 **IP**（Make 的出口 IP 可在 Make docs 查到）。
