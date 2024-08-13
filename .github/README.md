<!-- markdownlint-restore -->
<div align="center">

# ZenlessZoneZero - OneDragon

# **绝区零 - 一条龙**

<div>
    <img alt="platform" src="https://img.shields.io/badge/platform-Windows-blueviolet">
    <img alt="commit" src="https://img.shields.io/github/commit-activity/m/DoctorReid/ZenlessZoneZero-OneDragon?color=blue">
</div>
<div>
    <img alt="stars" src="https://img.shields.io/github/stars/DoctorReid/ZenlessZoneZero-OneDragon?style=social">
    <img alt="GitHub all releases" src="https://img.shields.io/github/downloads/DoctorReid/ZenlessZoneZero-OneDragon/total?style=social">
</div>
<br>

基于 绝区零 && 图像识别 && 一条龙框架，适用于 PC 端，一键完成日常任务

<font color=pink>

无修改游戏、读取内存等作弊行为。低调学习的好学生应该不会被米哈游老师抓

</font>

如果喜欢本项目，可右上角送作者一个`Star` ✨

唯一指定 QQ 群 `861603314`

</div>
</br>
<!-- markdownlint-restore -->

## 支持功能

- **战斗：** 一键赋予自动战斗的灵魂
- **闪避：** 拥有多种闪避方式供你选择
- **日常：** 完成每日任务，收派委托，刮刮乐
- **打本：** 每日副本
- **空洞：** 制作中，敬请期待~

## 安装方式

以下方式选择其一即可

### 1.1.使用自己的 Python 环境

（新手建议使用第二种）

1. 创建你自己的虚拟环境
2. `git clone git@github.com:DoctorReid/ZenlessZoneZero-OneDragon.git`
3. `pip install -r requirements-prod.txt`
4. 运行 （以下二选一）
   - 复制 `env.sample.bat`，重命名为 `env.bat`，并修改内容为你的虚拟环境的 python 路径，使用 `app.bat` 运行。
   - 将`src`文件夹加入环境变量`PYTHONPATH`，执行 `python src/zzz_od/gui/app.py` 。

### 1.2.使用安装器

使用安装器的话，不要放在包含空格的目录下

1. 从 [最新 Release](https://github.com/DoctorReid/ZenlessZoneZero-OneDragon/releases/latest) 中下载 `ZZZ-OD-X.Y.Z.zip` (X.Y.Z 为版本号)
2. 选择一个完整的英文目录，右键解压 `提取到当前位置`
3. 运行 `installer.exe`，选择 `一键安装`。如果无法同步代码，请在【设置】中填入你的网络代理。安装过程可能需要 5~10 分钟，请耐心等待。
4. 在安装器上点击`启动一条龙`，或手动运行 `app.bat`

### 前置说明

**使用前请先认真阅读以下内容**

1. 脚本存放的完整路径，只能是 **英文**，注意是完整路径，不只是脚本的文件夹。即从盘符（例如 C:\）开始不能有任何中文，包括 windows 中文用户名文件夹。如果你不清楚自己的路径是否有中文，在文件夹的地址栏上单击就可以看到。
2. 使用 **管理员** 权限运行脚本，否则可能无法发送键盘和鼠标指令。
3. 游戏内需要设置成 16:9 的分辨率，即 `1920*1080` 或 `2560*1440` 或 `3840*2160`，**优先** 选 **窗口模式**。选择 **全屏模式** 时，需保证你的 **屏幕** 分辨率和 **游戏** 分辨率都是 16:9 的。
4. 多屏幕的需要将游戏窗口放在 1 号屏。
5. 由于使用的是图像识别，请确保游戏画面完整在屏幕内，且游戏画面没有任何遮挡（帧率显示、windows 未激活水印等均有可能导致脚本出错）。游戏画质越好，脚本出错的几率越低。
6. 同时，请不要开启会改变画面像素值的功能或设置，例如
   - 系统层面 - windows 系统的颜色配置文件、校准显示器颜色、颜色管理、HDR 等。
   - 驱动层面 - 显卡驱动控制面板里的游戏滤镜等。
   - 设备层面 - 显示器的护眼模式、色彩模式、色温调节、HDR 等。
7. 如果游戏内进行过改键，请到脚本设置中对应修改。
8. 国际服需要在【设置】-【游戏设置】中更改区服后使用。

另可参考 [常见问题排查](https://kdocs.cn/l/cbSJUUNotJ3Z)

## 功能说明

### 自动闪避

**手残救星，只管输出即可**

判断游戏画面，出现黄光/红光后进行自动闪避，可设置成切人格挡，闪 A 切人(双反)，甚至自定义指令。[详细说明](https://github.com/DoctorReid/ZenlessZoneZero-OneDragon/wiki/%E5%8A%9F%E8%83%BD-%E9%97%AA%E9%81%BF%E5%8A%A9%E6%89%8B)

支持手柄，参考[文档](https://github.com/DoctorReid/ZenlessZoneZero-OneDragon/wiki/%E5%85%B6%E5%AE%83-%E6%89%8B%E6%9F%84%E6%94%AF%E6%8C%81)安装所需依赖。

注意: 不同响应速度的机器、不同的角色需要的按键手法不一样，特别是按键的间隔。 所以默认的配置未必适用所有情况，请按自身情况调整配置文件。

由于目前游戏机制(bug?)，切人是有可能切乱的，例如带丽娜的队伍。详细参考[B 站视频](https://www.bilibili.com/video/BV1JwaYeYEQo)

## 免责声明

- 本项目仅供学习交流使用。

- 开发者团队拥有本项目的最终解释权。

- 使用本项目产生的所有问题与本项目与及开发者团队无关。

- 若您遇到商家使用本软件进行代练并收费，产生的任何问题及后果与本软件无关。

### 贡献/参与者

感谢所有参与到开发的朋友们~

![Contributors](https://contributors-img.web.app/image?repo=DoctorReid/ZenlessZoneZero-OneDragon&max=1314520&columns=15)

## 赞助

如果喜欢本项目，可以为作者的赞助一点狗粮~

感谢 [小伙伴们的支持](https://github.com/DoctorReid/OneDragon-Thanks)

<img alt="赞助" src="./image/sponsor.png" width="512" height="256" />
