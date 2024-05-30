





## 安装依赖
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