# steam_watcher

> TODO: 补充运行截图

参考了 [SteamWatcher](https://github.com/SonodaHanami/Steam_watcher) 以及 [Lancercmd](https://github.com/Lancercmd) 和 [DiheChen](https://github.com/DiheChen) 的群 Bot steam 订阅功能演示

实现了
- [x] 通过 steamid 订阅用户正在玩的游戏
- [x] 通过 steamid 删除订阅
- [x] 查看当前群内订阅的用户及游戏状态
- [x] 查看当前群内订阅用户谁在玩游戏


## 配置说明

修改 `config.copy.toml` 为 `config.toml` 并根据提示填入自己的 steam api key

---

## 存储结构说明

`json/group_subscribe.json` 用于存储群订阅信息, 示例

```json
{
    "29797xxx": [
        "765611988149xxxxx",
        "76561198826xxxxxx",
        "76561198842xxxxxx",
        "76561198868xxxxxx",
    ],
    "1107755367": [
        "7656119884xxxxxxxx"
    ],
}   
```

将群号作为键, 以列表的形式存储订阅的用户 steamid

---

`json/steam_uid_game.json` 用于存储用户正在玩的游戏, 示例

```json
{
    "7656119881xxxxx": null,
    "7656119882xxxxx": "Counter-Strike: Global Offensive",
}
```

将用户 steamid 作为键, 以游戏名称字符串的形式存储用户正在玩的游戏名称, `null` 表示用户不在游戏中

---

`json/steam_uid_nickname.json` 用于存储用户昵称, 示例

```json
{
    "7656119881xxxxx": "xxx",
    "7656119882xxxxx": "xxx",
}
```

将用户 steamid 作为键, 以字符串的形式存储用户昵称

---

