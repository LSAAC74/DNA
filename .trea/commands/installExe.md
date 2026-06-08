请帮助我将当前 Python 项目打包成一个独立的 DnaGui.exe 可执行文件，并在打包完成后自动清理缓存。请按以下步骤操作：

1. **环境检查**
   - 确认当前项目根目录下有需要打包的 Python 入口文件（如 main.py、app.py）
   - 检查是否已安装 PyInstaller，如果没有，请执行：`pip install pyinstaller`

2. **分析项目依赖**
   - 扫描项目中的 import 语句，识别需要打包的第三方库
   - 如果存在 requirements.txt，请先执行 `pip install -r requirements.txt`

3. **执行打包命令（带 --clean 参数）**
   - 使用 PyInstaller 打包，基础命令格式：
     `pyinstaller --onefile --clean --name "程序名称" 入口文件.py`
   - 参数说明：
     - `--onefile`：打包成单个 exe 文件
     - `--clean`：打包前清理旧的临时文件（PyInstaller 缓存）
     - `--console`：显示控制台窗口（命令行程序用）
     - `--noconsole`：隐藏控制台窗口（GUI 程序用）
     - `--name`：指定生成的 exe 文件名
     - `--icon=图标.ico`：如有图标文件，添加自定义图标

4. **处理特殊依赖**
   - 如果项目使用了隐藏导入，自动添加 `--hidden-import` 参数
   - 如果使用了静态文件，请询问我是否需要使用 `--add-data` 一并打包

5. **打包完成后自动清理缓存**
   - 删除 `build/` 文件夹：`rmdir /s /q build`（Windows）
   - 删除 `.spec` 配置文件：`del /q 程序名.spec`（Windows）
   - 提示我：exe 文件已生成在 `dist/` 文件夹中，请勿删除此文件夹
   - 注意：只删除 build 和 spec 文件，保留 dist 文件夹和其中的 exe

6. **输出结果**
   - 告诉我 exe 文件的完整路径
   - 提示我：如果以后需要修改配置重新打包，可以将 `.spec` 文件保留或重新生成

注意事项：
- 打包后的 exe 文件较大（几十 MB），这是正常的
- 首次打包速度较慢，后续有 --clean 参数会清理旧缓存
- 打包完成后，临时缓存（build 文件夹、spec 文件）会被自动删除