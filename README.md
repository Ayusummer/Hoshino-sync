<!--
 * @Author: your name
 * @Date: 2021-03-02 22:18:32
 * @LastEditTime: 2021-03-02 22:21:02
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \HoshinoBot\README.md
-->
- 个人自用的魔改版hoshino
- 初衷是减轻会战用bot的负担而想在另一台服务器上搭个bot将一些压力大的服务以及后续更新的非pcr相关的服务分担过来
- 由于想留下更新记录以及wiki又不想本地服务器都做改动所以fork了一个自用的仓库

# 部署说明

## 安装 python3.8

> 3.8 只是个人喜好, 平时使用的某些库尚未支持 3.9 及以上  
> ubuntu2004 拉取 python3-pip 默认也是 3.8

### ubuntu

```bash
# 更新源
apt-get update
# 安装 python3
apt install python3-pip
```

---

### windows

> windows 下可以使用 anaconda 管理 python 环境  
> 需要注意的是, 使用 Anaconda Navigator 或者 conda 环境操作时需要关掉梯子, 否则可能会报 host 错误

[安装包](https://ayusummer-my.sharepoint.com/:u:/g/personal/233_ayusummer_onmicrosoft_com/EeoLeabp6RtDnVkgJ46y_fIB9gqFsNbpyO8BqSZzQv_r3w?e=NwyQXf)

安装完成后打开 `Anaconda Navigator`:

![image-20220523093633147](http://cdn.ayusummer233.top/img/202205230936469.png)

#### Anaconda 换源

> [anaconda修改国内源 - 余者皆可 - 博客园 (cnblogs.com)](https://www.cnblogs.com/yuvejxke/p/13169172.html)

- 打开 `anaconda prompt`   
  ![20220113131937](http://cdn.ayusummer233.top/img/20220113131937.png)  
  ![20220113132007](http://cdn.ayusummer233.top/img/20220113132007.png)

- 执行以下命令来配置清华源：
  ```shell
  conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
  conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge
  conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/msys2/
  ```

  配置清华源是为了后续使用 `pip` 命令安装 python 库时快些, 不配置换源而直接使用默认源的话在墙内容易超时报错

---

#### 新建一个 conda 环境

打开 `Anaconda Navigator -> Environments` 在环境列表底部按钮中找到 `Create` 并点击

![image-20220517153334579](http://cdn.ayusummer233.top/img/202205171533981.png)

为新环境命一个名(英文命名, 尽量简短些, 之后激活要用)

> 这里选择了 Python 3.8.13, 不上 3.9 或者 3.10 主要是因为有一些三方库更新没跟上, 不一定支持 python3.9 及以上

![image-20220517153442365](http://cdn.ayusummer233.top/img/202205171534732.png)

在命令行中使用 conda 环境可以使用如下指令激活:

```bash
conda activate 环境名
```

![image-20220517153733464](http://cdn.ayusummer233.top/img/202205171537691.png)

---

## 开发环境配置(VSCode)

[VSCode 安装包](https://ayusummer-my.sharepoint.com/:u:/g/personal/233_ayusummer_onmicrosoft_com/EazLjY72FsFBvNS9qfiXUNsBoncvju914TnopNKvIkyU_A?e=H46sLL)

用于编辑与运行 python 程序, 选择 VSCode 主要是其比较轻量, 启动比较快, 用起来比较顺手, 且插件市场庞大, 对于许多语言都有插件支持, 按需下载

比起安装 python 解释器自带的 IDLE 友好许多, 又不会像 Pycharm 一样庞大/启动慢/占资源, 作为平时写点小脚本, 小玩意儿来说完全够用

#### VSCode 扩展安装

- 汉化插件

  ![image-20220113132736972](http://cdn.ayusummer233.top/img/202201131327282.png)

- Python 相关基础插件

  ![image-20220113132900552](http://cdn.ayusummer233.top/img/202201131329644.png)

- jupyter 插件

  ![image-20220113132930881](http://cdn.ayusummer233.top/img/202201131329984.png)

  使用 Jupyter 的好处在于可以边写笔记边写代码, 如下图所示, 在笔记中可以插入代码块并运行及显示

  ![image-20220113133105876](http://cdn.ayusummer233.top/img/202201131331074.png)

- Markdown 插件

  ![image-20220113133332281](http://cdn.ayusummer233.top/img/202201131333467.png)

- 命令行插件 Terminal

  ![image-20220113134443536](http://cdn.ayusummer233.top/img/202201131344681.png)

  用于在 VSCode 中打开 powershell 执行命令

  ![image-20220113134623777](http://cdn.ayusummer233.top/img/202201131346049.png)

----

## clone 仓库

在 VSCode 中打开 Terminal 执行以下命令

```bash
git clone https://github.com/Ayusummer/HoshinoBot.git --depth 1
```

使用 `--depth` 主要是因为由于之前错误上传资源文件, 导致仓库 `.git` 文件比较大, 如果拉取所有 git 记录的话会比较慢

---
## 配置虚拟环境

安装并创建 virtualenv (继续在 Terminal 下执行命令)

> windows 下使用 anaconda 请先使用 `conda activate xxx` 激活 conda 环境


```bash
# 切换到项目根目录
cd HoshinoBot

# 更新当前 pip
pip install --upgrade pip

# 安装 virtualenv
pip install virtualenv

# 创建 virtualenv
virtualenv env

# 激活虚拟环境(ubuntu)
source env/bin/activate
# 激活虚拟环境(windows)
env/Scripts/activate.bat
```

虚拟环境激活后此时命令行内会看到 `(env)`

![image-20220523153808633](http://cdn.ayusummer233.top/img/202205231538777.png)

> windows 环境下使用 anaconda 时, 在前面的步骤我们已经配置好了换源   
> ubuntu 环境下需要再配置下源:  
> 在 `/ubuntu/用户/` 路径下创建 `.pip` 文件夹, 在其中创建 `pip.conf` 文件  填入:
> ```bash
> [global]
> index-url = https://mirrors.aliyun.com/pypi/simple/
> [install]
> trusted-host=mirrors.aliyun.com
> ```  
> 或者使用清华源:
> ```
> [global]
> index-url = https://pypi.tuna.tsinghua.edu.cn/simple
> [install]
> trusted-host=pypi.tuna.tsinghua.edu.cn
> ```

安装依赖

```bash
pip install -r requirements.txt
```