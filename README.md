StockFlow
StockFlow 是一款用于进货统计与活动完成度的桌面应用软件，旨在帮助用户管理品牌进货信息、设置活动目标、跟踪进货进度，并导出账单统计数据。软件使用 Python 开发，基于 PyQt5  框架和 SQLite 数据库。
功能

进货管理：记录不同品牌的进货信息（品名、规格、数量、单价、总金额、日期）。
活动目标：设置每月活动目标（总金额或单品数量），计算完成进度和返现金额。
进度查看：实时查看当月进货情况和活动目标完成进度。
账单导出：导出指定时间段的账单统计数据（支持 Excel/CSV 格式）。

安装
环境要求

Python 3.8 或以上版本
PyQt5
SQLite（内置于 Python）

安装步骤

克隆项目：
git clone <repository-url>
cd stockflow


创建并激活虚拟环境：
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows


安装依赖：
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

安装完成后，检查是否成功安装了 requirements.txt 中的依赖（PyQt5、pandas 和 openpyxl）。
pip list


运行程序：
python main.py



使用说明

启动程序后，进入“添加品牌”界面，添加需要管理的品牌。
在“品牌进货信息详情”界面输入进货记录。
使用“筛选”功能查看指定时间段和品牌的进货情况。
在“单月活动信息”界面设置活动目标并跟踪进度。
导出账单数据以查看统计信息。

项目结构

main.py：程序入口文件。
ui/：存放界面代码（PyQt6 实现）。
database/：存放数据库操作代码（SQLite）。
models/：存放数据模型。
utils/：存放工具函数（如导出功能）。
data/：存放 SQLite 数据库文件。

开发

技术栈：Python, PyQt6, SQLite
依赖管理：requirements.txt
数据库：SQLite（data/stockflow.db）

贡献
欢迎提交问题和建议！请通过 GitHub Issues 联系。
许可证
MIT 许可证
