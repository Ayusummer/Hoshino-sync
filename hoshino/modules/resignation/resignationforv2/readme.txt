这是一个使用yobot的数据生成离职报告的hoshino插件，仅供娱乐
感谢魔法书大佬帮我测试及讲解游戏机制
因插件使用过程中会读取yobot数据库，因程序运行故障导致数据库损坏本人概不负责

安装说明：
此插件试用于hoshino V2，V1版见另一文件夹

0. 按照hoshino的说明创建模块目录，将resignation文件夹放入模块目录，或者直接放到已有模块的目录下。确保路径结构是modules/模块目录名/resignationforv2
1. 安装依赖 matplotlib，pillow 如果你成功安装过hoshino，这两个库应该已经装好了，这一步pass
2. 为matplotlib安装中文字体。如果你是Windows系统，这一步应该不需要做。linux系统请先使用 pip show matplotlib找到matplotlib的安装位置，并将msyh.ttf文件复制matplotlib/mpl_data的font目录下
3. 为pillow提供中文字体，将msyh.ttf文件移到resignationforv2里应该就可以 注意：最后字体文件要和__init__.py和data_source.py在同一目录
3.在__init__.py里修改yobot的网址
4.在data_source.py里修改yobot的数据库路径，linux系统请确认相关文件的访问权限问题

ps：
不同设备可能出现显示与我的预设不同的结果，请尝试微调__init__.py里的坐标参数
注意yobot设置中要开放api访问
本人对游戏机制了解不多，所以计算方式上可能会有不正确的地方

							——by 倚栏待月