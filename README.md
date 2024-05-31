# 5GNetBar 是什么?
5GNetBar 是一个用于在mac状态栏中显示5G网络信号强度和cpu温度占用的小工具.

支持设备: 
5G长城随身wifi(使用类似系统的),有无高级后台是否会影响未测过.
使用默认用户(admin)和密码(admin)登录获取数据,暂不支持自定义用户和密码.

> 主要用来寻找最佳的信号位置,以及监控设备的温度及负载. 5G信号强度和设备温度是有关联的,信号强度越弱,设备温度越高.

![iShot_2024-05-30_16.47.34.png](media%2FiShot_2024-05-30_16.47.34.png)
![iShot_2024-05-30_16.48.52.png](media%2FiShot_2024-05-30_16.48.52.png)
![iShot_2024-05-30_16.49.12.png](media%2FiShot_2024-05-30_16.49.12.png)

## 下载使用
[下载地址](https://github.com/lvusyy/5GNetBar/releases/tag/v1.0.8.3)
> 注意: 下载后需要解压,然后将解压后的文件拖到桌面上打开一次后就可以正常使用了,注意先退出(退出的话点击Quit即可).
 
>如果想放到*应用中心*就要用*访达*,从桌面把"5GNetBar"拖拽到"应用程序"里面即可.



## 自行编译使用

### 安装依赖
建议使用虚拟环境
```bash
# 创建新的虚拟环境
conda create --name 5GNetBar python=3.10

# 激活新环境
conda activate 5GNetBar

# 安装依赖项
pip install pyobjc requests

```


## 打包成应用
### 安装pyinstaller
注意不要使用全局方式安装，否则可能会出现找不到模块的情况

`pip install pyinstaller`

### 命令行应用
```bash
pyinstaller --onefile --hidden-import=requests --hidden-import=Foundation --hidden-import=AppKit --hidden-import=objc 5GNetBar_app.py
```

### app应用
### 命令行方式创建/打包桌面应用
```bash
pyinstaller --name 5GNetBar --hidden-import=requests --hidden-import=Foundation --hidden-import=AppKit --hidden-import=objc 5GNetBar_app.py
```


### spec配置文件
```python
# -*- mode: python -*-

block_cipher = None

a = Analysis(['5GNetBar_app.py'],
             pathex=['/Users/duncanzat/PycharmProjects/5GNetBar'],
             binaries=[],
             datas=[],
             hiddenimports=['requests', 'Foundation', 'AppKit', 'objc'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='5GNetBar',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='5GNetBar')

app = BUNDLE(coll,
             name='5GNetBar.app',
             icon='/Users/duncanzat/PycharmProjects/5GNetBar/Myicon.icns',
             bundle_identifier=None)
```
### icns文件生成
安装 ImageMagick
```bash
brew install imagemagick
```

#### 转换图标格式
创建 iconset 文件夹：
```bash
mkdir MyIcon.iconset
```

转换并生成不同分辨率的图标：

假设你的源文件是 5gNetBar.webp，可以运行以下命令：

```bash
convert 5gNetBar.webp -resize 16x16 MyIcon.iconset/icon_16x16.png
convert 5gNetBar.webp -resize 32x32 MyIcon.iconset/icon_32x32.png
convert 5gNetBar.webp -resize 64x64 MyIcon.iconset/icon_64x64.png
convert 5gNetBar.webp -resize 128x128 MyIcon.iconset/icon_128x128.png
convert 5gNetBar.webp -resize 256x256 MyIcon.iconset/icon_256x256.png
convert 5gNetBar.webp -resize 512x512 MyIcon.iconset/icon_512x512.png
convert 5gNetBar.webp -resize 1024x1024 MyIcon.iconset/icon_1024x1024.png
```
将 iconset 文件夹转换为 icns 文件：

使用 iconutil 将 .iconset 文件夹转换为 .icns 文件：

```bash
iconutil -c icns MyIcon.iconset
```

这将生成 MyIcon.icns 文件。