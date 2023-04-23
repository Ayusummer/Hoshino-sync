# mhw

怪猎集会码记录工具 + 游戏上下线提醒

---

## 存储结构说明

由于数据量不大, 且仅需要保存近两天的集会码因此没做数据库, 直接用json文件存储

唯一的 json 为 `json/date_code.json` , 用于存储日期以及集会信息

具体结构如下:

```json
{
    "2023-04-18": [
        {
            "code": "n6nhkZPWDsZE",
            "nickname": "\u6e38\u620f\u9ad8\u624b\u6cc9\u6b64\u65b9",
            "note": "3\u7fa4-\u714c\u9ed1-\u9ed1\u72fc\u9e1f"
        },
        {
            "code": "c3@uTKhzD+tu",
            "nickname": "\u6e38\u620f\u9ad8\u624b\u6cc9\u6b64\u65b9",
            "note": "1\u7fa4-\u706d\u65e5"
        }
    ],
}
```

将日期作为键, 以列表的形式存储当天的集会信息

- `code(str)`: 集会码
- `nickname(str)`: 录入者昵称(群名片)
- `note(str)`: 备注信息


