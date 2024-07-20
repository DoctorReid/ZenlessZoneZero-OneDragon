# Zenless Zone Zero - One Dragon

__绝区零 - 一条龙__

基于 绝区零 && 图像识别 的相关学习资料，适用于PC端。

无修改游戏、读取内存等作弊行为。低调学习的~~好~~学生应该不会被米哈游老师抓。

学习后，你可以

- ~~领悟 `图像识别` 相关知识~~
- 领悟 `自动闪避` 能力(测试中)
- 领悟 `自动每日` 的护肝方法 (开发中)

如果喜欢本项目，可右上角送作者一个```Star```

## 学习方式

### 使用自己的Python环境

1. 创建你自己的虚拟环境
2. `git clone git@github.com:DoctorReid/ZenlessZoneZero-OneDragon.git`
3. `pip install -r requirements-prod.txt`
4. 运行 （以下二选一）
   - 复制 `env.sample.bat`，重命名为 `env.bat`，并修改内容为你的虚拟环境的python路径，使用 `app.bat` 运行。
   - 将`src`文件夹加入环境变量`PYTHONPATH`，执行 `python src/zzz_od/gui/app.py` 。


### 常见报错

#### 动态链接库(DLL)初始化例程失败

安装最新版的 [Microsoft Visual C++](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### 前置说明

- 游戏画面的分辨率需要是 `16:9`，即 `1920*1080` 或 `2560*1440` 或 `3840*2160`
- 需管理员权限运行，否则可能无法发送按键和鼠标指令
- 国际服需要在【设置】-【游戏设置】中更改区服后使用


## 功能说明

### 自动闪避

__手残救星，只管输出即可__

判断游戏画面，出现黄光/红光后进行自动闪避，可设置成切人格挡，闪A挡。

可自行配置更多自定义指令，见 [功能-自定义指令](https://github.com/DoctorReid/ZenlessZoneZero-OneDragon/wiki/%E5%8A%9F%E8%83%BD-%E8%87%AA%E5%AE%9A%E4%B9%89%E6%8C%87%E4%BB%A4)。

支持使用GPU运算，模型运行在50ms内应该就能正常使用。（整个闪光过程大概持续100ms）


## 免责声明

本项目仅供学习交流使用。

开发者团队拥有本项目的最终解释权。

使用本项目产生的所有问题与本项目与及开发者团队无关。


## 赞助

如果喜欢本项目，可以为作者的赞助一点狗粮~

感谢 [小伙伴们的支持](https://github.com/DoctorReid/OneDragon-Thanks)

![赞助](./image/sponsor.png)
