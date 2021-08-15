# Reloader
* nonebot >= 1.5.0

linux系统下的使用说明（windows请看到第四步为止）：

1. 解压缩文件到插件目录modules下

2. 在 config/__bot__.py的模块列表里加入 reload

3. 修改HoshinoBot下的run.py为(use_reloader=True)

4. 重启HoshinoBot （如果你是linux系统，请最后一步执行该步骤）

5. 在run.py的最上面一行添加 
   #! /usr/bin/env python
   （如果你是python3就改成python3）

6. 安装dos2unix：
   sudo apt-get install dos2unix
   （此为ubuntu系统下的指令，其他版本系统请自行查阅安装方法）
   
7. 使用dos2unix转换格式
   sudo dos2unix run.py
   
8. 转换完成，即可正常使用重启指令来重载星乃



