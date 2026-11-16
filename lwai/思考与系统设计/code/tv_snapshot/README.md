# TradingView 发布页图表快照解析

脚本发布页的图表是作者保存的快照，HTML 里嵌着整张图的状态：K 线、每个指标逐根的绘图值、标签/方框/线条、信息表，以及保存时的输入参数。这些是任何访客打开页面都会下载的公开数据，不含源码。

```bash
curl -sS -A "Mozilla/5.0" -o page.html "https://www.tradingview.com/script/<ID>/"
python3 decode_snapshot.py page.html snap.json          # 解出快照 JSON，并打印结构
python3 snap_to_csv.py snap.json out/ <ID> page.html    # 每个指标一个 CSV（OHLCV + 各绘图列）、图形 JSON、实际参数
python3 find_metainfo.py page.html "<scriptIdPart>"     # 单独查看绘图列的名称和顺序
python3 extract_meta.py page.html                       # 输入参数定义（名称、默认值、分组、提示）和警报文案
```

CSV 列名格式为 `名称|类型|plot_id`。`*_graphics.json` 里的坐标 `x` 是 `indexes` 数组的下标，`indexes[x]` 才是 K 线的 `index`。
