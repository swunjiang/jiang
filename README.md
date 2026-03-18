# jiang
learning some knowledge and record it

## B站视频评论下载工具 (Bilibili Comment Downloader)

这个py程序能够下载B站视频的评论以csv格式保存。

### 功能
- 支持通过视频链接（含BV号）下载评论
- 自动获取视频标题
- 下载一级评论和二级评论（楼中楼）
- 支持置顶评论
- 导出为 CSV 格式，包含用户名、内容、时间、点赞数、评论层级

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用方法

```bash
python bilre2.py
```

运行后按提示输入B站视频链接，例如：
```
https://www.bilibili.com/video/BVxxxxxxxxxx
```

评论将保存到 `bilibili_comments/` 目录下，文件名格式为：
```
<视频标题>_<BV号>_<时间戳>_comments.csv
```

### CSV 字段说明

| 字段 | 说明 |
|------|------|
| 用户 | 评论者用户名 |
| 评论内容 | 评论正文（置顶评论前缀`[置顶]`） |
| 时间 | 发布时间（格式：YYYY-MM-DD HH:MM:SS） |
| 点赞数 | 评论获得的点赞数量 |
| 评论层级 | 0=置顶，1=一级评论，2=二级评论 |
