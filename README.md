<!--
 * @Author: your name
 * @Date: 2021-03-02 22:18:32
 * @LastEditTime: 2021-03-02 22:21:02
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \HoshinoBot\README.md
-->
个人自用的魔改版 hoshino

> 源仓库链接:  
> [Ice-Cirno/HoshinoBot: A qqbot for Princess Connect Re:Dive (and other usage :) (github.com)](https://github.com/Ice-Cirno/HoshinoBot)

初衷是减轻会战用bot的负担而想在另一台服务器上搭个bot将一些压力大的服务以及后续更新的非 pcr 相关的服务分担过来

由于想留下更新记录以及 wiki 又不想本地服务器都做改动所以 fork 了一个自用的仓库

由于剔除了 PCR 相关功能加上由于太懒不拉更新导致后面完全无法和源仓库对齐, 所以有了这个仓库

[Wiki 页面](https://github.com/Ayusummer/Hoshino-sync/wiki) 为各功能模块的说明

> 仓库功能模块大多来源于社区插件整合, 来源有在 [Wiki 页面](https://github.com/Ayusummer/Hoshino-sync/wiki) 中说明  
> 更多插件请参阅:   
> [pcrbot/HoshinoBot-plugins-index: HoshinoBot 插件索引 (github.com)](https://github.com/pcrbot/HoshinoBot-plugins-index)

---

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
git clone https://github.com/Ayusummer/Hoshino-sync.git --depth 1
```

使用 `--depth` 主要是因为由于之前错误上传资源文件, 导致仓库 `.git` 文件比较大, 如果拉取所有 git 记录的话会比较慢

---
## 使用 poetry 配置虚拟环境

> [Introduction | Documentation | Poetry - Python dependency management and packaging made easy (python-poetry.org)](https://python-poetry.org/docs/#windows-powershell-install-instructions)
>
> [Introduction | master | Documentation | Poetry - Python dependency management and packaging made easy (python-poetry.org)](https://python-poetry.org/docs/master/#installing-with-the-official-installer)

Poetry 提供了一个自定义的安装程序, 通过解构 Poetry 的依赖关系, 将 Poetry 与系统的其他部分隔离开, 这是一种推荐的安装方式;

### `osx / linux / bashonwindows install instructions`:

```shell
curl -sSL https://install.python-poetry.org | python3 -
```

#### poetry安装慢的解决方案

> [Python Poetry安装慢的解决办法（转载） - tahitimoon - 博客园 (cnblogs.com)](https://www.cnblogs.com/tahitimoon/p/15113082.html)
>
> [Introduction | master | Documentation | Poetry - Python dependency management and packaging made easy (python-poetry.org)](https://python-poetry.org/docs/master/#installing-with-the-official-installer)

---

#### 配置环境变量

打开 `/root/.bashrc` 并在最后一行添加

```bash
export PATH="/root/.local/bin:$PATH"
```

加载环境变量

```bash
source /root/.bashrc
```

查看 poetry 版本

```bash
poetry --version
```



### `windows powershell install instructions`:

```powershell
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -
```

![image-20220527065741632](http://cdn.ayusummer233.top/img/202205270657858.png)

poetry 会自动添加环境变量, 安装完后重启 `powershell`, 检查下 poetry 版本:

```powershell
poetry --version
```

---

### 配置项目环境

配置 poetry 使得虚拟环境在项目根目录下生成(`.venv`)

```powershell
poetry config virtualenvs.in-project true
```

配置虚拟环境并安装依赖

```bash
# 切换到项目根目录
cd HoshinoBot

# 安装依赖
poetry install
```

将 `hoshino/config_example` 目录中的 `config_example` 重命名为 `config` (或者拷贝出一个 `config_example` 再重命名)

根据 `config` 目录下的文件中的提示进行项目配置

```bash
# 激活虚拟环境
poetry shell

# 运行 run.py
python run.py
```

---

### invalid hashes(ubuntu)

> [Invalid hashes errors on fresh install · Issue #4883 · python-poetry/poetry (github.com)](https://github.com/python-poetry/poetry/issues/4883)

```bash
curl -sSL https://install.python-poetry.org | python3 - --uninstall
# if the above command tells you poetry isn't installed, try this instead (poetry's previous installer has recently been deprecated):
# curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - --uninstall
rm -r ~/.cache/pypoetry
# if your poetry cache is somewhere else, this tells you where: poetry config --list
curl -sSL https://install.python-poetry.org | python3 -
```

像这样重新装下 poetry 然后重新运行 `poetry install` 就好了
