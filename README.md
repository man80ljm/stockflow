
# Stockflow 软件说明

## 概述
`Stockflow` 是一款基于 PyQt5 的库存管理系统，专为品牌进货管理、活动跟踪和数据导出设计。用户可以通过直观的图形界面管理品牌、进货记录、活动信息，并支持将数据导出为 Excel 文件。本文档提供安装依赖、国内镜像源配置、打包命令以及软件功能的相关信息。

---

## 依赖安装

### 所需包组
以下是运行和打包 `Stockflow` 所需的所有 Python 包。请确保在虚拟环境中或全局环境中安装这些依赖：

- `PyQt5`：用于图形用户界面 (GUI) 开发。
- `pandas`：用于数据处理和分析。
- `openpyxl`：用于 Excel 文件的读写支持。
- `pyinstaller`：用于将 Python 脚本打包为可执行文件。

### 安装命令
在终端或 PowerShell 中运行以下命令安装依赖：

```bash
pip install PyQt5 pandas openpyxl pyinstaller
```

### 国内镜像源配置
为加速下载，建议使用国内镜像源（如清华源、阿里源）。以下是常用镜像源配置示例：

- **清华源**：
  ```bash
  pip install PyQt5 pandas openpyxl pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

- **阿里云**：
  ```bash
  pip install PyQt5 pandas openpyxl pyinstaller -i http://mirrors.aliyun.com/pypi/simple/
  ```

- **豆瓣源**：
  ```bash
  pip install PyQt5 pandas openpyxl pyinstaller -i http://pypi.douban.com/simple/
  ```

**注意**：
- 在命令中添加 `-i` 参数后跟镜像源 URL。
- 建议使用虚拟环境（如 `venv` 或 `virtualenv`）以避免冲突：
  ```bash
  python -m venv venv
  .\venv\Scripts\activate  # Windows
  source venv/bin/activate  # macOS/Linux
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
- 可创建 `requirements.txt` 文件，内容如下：
  ```
  PyQt5
  pandas
  openpyxl
  pyinstaller
  ```
  然后运行 `pip install -r requirements.txt`。

---

## 打包命令

### 打包环境准备
- 确保所有依赖已安装。
- 项目根目录为 `stockflow/`，包含 `main.py`、`ui/`、`database/` 等子目录。
- 用户需手动创建 `data` 目录（存放 `stockflow.db` 和 `debug.log`），路径为 `dist\data`。

### 打包命令
使用 PyInstaller 将 `stockflow` 打包为单一可执行文件，并隐藏 DOS 窗口。以下是完整命令：

```powershell
pyinstaller -F -w --name Stockflow --add-data "ui;ui" --add-data "database;database" --add-data "models;models" --add-data "utils;utils" --add-data "data;data" main.py
```

**参数说明**：
- `-F`：生成单一 `.exe` 文件。
- `-w`：运行时关闭 DOS 窗口。
- `--name Stockflow`：输出文件名 `Stockflow.exe`。
- `--add-data "ui;ui"`：包含 `ui` 目录（Windows 使用 `;` 分隔）。
- `--add-data "database;database"`：包含 `database` 目录。
- `--add-data "models;models"`：包含 `models` 目录。
- `--add-data "utils;utils"`：包含 `utils` 目录。
- `--add-data "data;data"`：包含 `data` 目录（即使为空，防止路径问题）。
- `main.py`：项目入口文件。

**输出**：
- 打包完成后，`dist\Stockflow.exe` 生成于 `d:\stockflow\dist\` 目录。

### 优化打包（可选）
若运行 `Stockflow.exe` 出现依赖错误（如 `pandas` 或 `openpyxl`），需生成并修改 `Stockflow.spec`：
1. 运行：
   ```powershell
   pyinstaller -F -w main.py
   ```
2. 编辑 `Stockflow.spec`，添加：
   ```python
   hiddenimports=['pandas', 'openpyxl', 'PyQt5'],
   ```
3. 重新打包：
   ```powershell
   pyinstaller Stockflow.spec
   ```

---

## 软件功能介绍

### 主要功能
`Stockflow` 提供以下核心功能，旨在简化库存管理和数据分析：

1. **品牌管理**：
   - 添加、删除品牌。
   - 通过图形界面显示品牌列表，支持右键删除操作。

2. **进货详情**：
   - 查看品牌关联的进货记录，支持按年月过滤。
   - 支持分页浏览（每页 20 条记录）。
   - 提供“增加”、“当月活动”、“活动完成情况”、“支出情况”和“账单导出”功能。
   - 双击备注列可编辑，右键支持修改和删除记录。

3. **数据导出**：
   - 将进货记录导出为 Excel 文件，保存在项目 `data` 目录下。
   - 文件名格式为 `{brand_name}_{year}年{month}月_进货详情.xlsx`。

4. **活动管理**：
   - 查看单月活动信息，包括总目标和单品目标。
   - 支持活动完成情况和支出情况的详细分析。

### 使用步骤
1. 解压 `Stockflow` 文件到任意目录（如 `D:\Stockflow`）。
2. 在 `dist` 目录下创建 `data` 文件夹。
3. 双击 `Stockflow.exe` 运行程序。
4. 使用界面添加品牌、查看进货详情或导出数据。

### 注意事项
- 运行前必须手动创建 `data` 目录，否则程序会因无法创建 `stockflow.db` 或 `debug.log` 而报错。
- 数据库文件 `stockflow.db` 和日志文件 `debug.log` 将存储在 `data` 目录中。
- 建议定期备份 `data` 目录以防止数据丢失。

---

## 联系与反馈
- **当前日期**：2025年6月10日
- 如有问题或建议，请通过 [您的联系方式] 反馈。
- 项目开源仓库：[如有请提供 URL]。

---

### 总结
- **依赖**：`PyQt5`、`pandas`、`openpyxl`、`pyinstaller`，建议使用国内镜像源加速安装。
- **打包**：使用 `pyinstaller -F -w ...` 命令生成单一 `Stockflow.exe`，需手动创建 `data` 目录。
- **功能**：品牌管理、进货详情、数据导出、活动管理，界面友好易用。

请根据上述内容创建或更新 `README.md` 文件。如需调整内容或添加更多细节（例如截图、具体功能说明），请告知，我将进一步完善！