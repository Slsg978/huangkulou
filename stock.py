from typing import List, Tuple

import requests
import pandas as pd
import json
import time
import pymysql
from sqlalchemy import create_engine
# 配置请求头，模拟浏览器访问，避免被风控

url = 'https://push2.eastmoney.com/api/qt/clist/get'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://quote.eastmoney.com/'
}
conn = pymysql.connect(
    host='localhost',      # 数据库地址
    port=3306,            # 端口，默认3306
    user='root',      # 用户名
    password='123456',  # 密码
    database='local',  # 数据库名
    charset='utf8mb4'     # 字符集
)
SECTOR_SQL = """
INSERT INTO `local`.`sector_info` ( `sector_code`, `sector_name`, `latest_price`, `change_percent`, `total_market_cap`, `change_value`, `turnover_rate`, `leader_stock_code`, `leader_stock_name`, `leader_stock_change_percent`, `up_numbe`, `down_numbe`,`trade_date`) 
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

STOCK_SQL = """
INSERT INTO `local`.`stock_capital_flow` (`type`,`stock_code`, `stock_name`, `related_code`, `related_name`, `latest_price`, `change_percent`, `main_net_inflow`, `main_net_inflow_ratio`, `super_large_net_inflow`, `super_large_net_inflow_ratio`, `large_net_inflow`, `large_net_inflow_ratio`, `medium_net_inflow`, `medium_net_inflow_ratio`, `small_net_inflow`, `small_net_inflow_ratio`, `change_percent_5d`, `main_net_inflow_5d`, `main_net_inflow_ratio_5d`, `super_large_net_inflow_5d`, `super_large_net_inflow_ratio_5d`, `large_net_inflow_5d`, `large_net_inflow_ratio_5d`, `medium_net_inflow_5d`, `medium_net_inflow_ratio_5d`, `small_net_inflow_5d`, `small_net_inflow_ratio_5d`, `change_percent_10d`, `main_net_inflow_10d`, `main_net_inflow_ratio_10d`, `super_large_net_inflow_10d`, `super_large_net_inflow_ratio_10d`, `large_net_inflow_10d`, `large_net_inflow_ratio_10d`, `medium_net_inflow_10d`, `medium_net_inflow_ratio_10d`, `small_net_inflow_10d`, `small_net_inflow_ratio_10d`, `trade_date`) 
VALUES (%s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


# 定义不同类型板块的筛选参数（行业/概念/地域）
BOARD_TYPES = {
    "行业板块": "m:90+t:2+f:!50",
    "概念板块": "m:90+t:3+f:!50",
    "地域板块": "m:90+t:1+f:!50"
}


def get_board_list(board_type_filter):
    """获取指定类型的所有板块（名称+代码）"""
    params = {
        'pn': 1,
        'pz': 1000,  # 一次性获取足够多的板块，覆盖所有类型
        'fields': 'f2,f3,f4,f8,f12,f13,f14,f20,f104,f105,f128,f140,f141,f136',  # f12=板块代码，f14=板块名称
        'fs': board_type_filter
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()  # 抛出HTTP错误
        data = json.loads(response.text)
        if data['data'] and data['data']['diff']:
            boards = data['data']['diff']
            save_sectors(boards.values())
            # for board in boards.values():
            #     print((board['f14'], board['f12']))
            return [(board['f14'], board['f12']) for board in boards.values()]
        else:
            return []
    except Exception as e:
        print(f"获取板块列表失败：{e}")
        return []

def save_sectors(rows: List[dict]):
    values = [
        (
            r.get("f12"), #sector_code
            r.get("f14"), #`sector_name`
            r.get("f2"),  #`latest_price` 最新价格
            r.get("f3"), # change_percent涨跌幅
            r.get("f20"), #`total_market_cap`, 总市值
            r.get("f4"), # `change_value` 涨跌额
            r.get("f8"), #`turnover_rate` 换手率
            r.get("f140"), #leader_stock_code
            r.get("f128"), #leader_stock_name
            r.get("f136"), #leader_stock_change_percent
            r.get("f104"), # `up_numbe`
            r.get("f105"), #, `down_numbe`
            '2025-12-30'
        )
        for r in rows
    ]

    with conn.cursor() as cursor:
        cursor.executemany(SECTOR_SQL, values)
    conn.commit()
    print(f"✅ sector_info 写入 {len(values)} 条")



def get_top_market_cap_company(board_code,board_name):
    """获取单个板块市值最大的公司名称"""
    page = 1

    try:

            params = {
                'pn': 1,  # 页码（page number），从1开始
                'pz': 5000,  # 每页条数（page size）
                'po': 1,  # 排序方式
                'np': 1,  # 是否需要分页
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',  # 固定token
                'fltt': 2,  # 字段格式
                'invt': 2,  # 投资类型
                'fid': 'f20',  # 排序字段
                'fs': f'b:{board_code}',  # 市场代码，例如：b:BK0420 表示板块
                'fields': "f14,f12,f13,f1,f2,f4,f3,f152,f128,f140,f141,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f109,f160,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183"
            }
            print(f"获取板块{board_code}信息")
            time.sleep(0.3)  # 增加延时，避免请求过快被限制
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = json.loads(response.text)
            if data['data'] and data['data']['diff']:
                boards = data['data']['diff']
                parse_stock(boards,board_code,board_name)
    except Exception as e:
        print(f"获取板块{board_code}的龙头公司失败：{e}")
        return '获取失败'

def parse_stock(rows,board_code,board_name):
    values = [
        (
            row.get("f13",None),     # stock_code
            row.get("f12",None),     # stock_code
            row.get("f14",None),     # stock_name
            board_code,
            board_name,
            clean_numeric(row.get("f2",None)),

            clean_numeric(row.get("f3",None)),      # change_percent
            clean_numeric(row.get("f62",None)),      # change_amount
            clean_numeric(row.get("f184",None)),     # open_price
            clean_numeric(row.get("f66",None)),     # high_price
            clean_numeric(row.get("f69",None)),     # low_price
            clean_numeric(row.get("f72",None)),     # prev_close
            clean_numeric(row.get("f75",None)),      # amplitude
            clean_numeric(row.get("f78",None)),      # volume
            clean_numeric(row.get("f81",None)),      # turnover
            clean_numeric(row.get("f84",None)),     # volume_ratio
            clean_numeric(row.get("f87",None)),
            # turnover_rate
            clean_numeric(row.get("f109",None)),     # total_market_cap
            clean_numeric(row.get("f164",None)),     # circulating_market_cap
            clean_numeric(row.get("f165",None)),      # pe_ratio
            clean_numeric(row.get("f166",None)),     # pe_ratio_ttm
            clean_numeric(row.get("f167",None)),     # pb_ratio
            clean_numeric(row.get("f168",None)),    # industry_pe
            clean_numeric(row.get("f169",None)),
            clean_numeric(row.get("f170",None)),
            clean_numeric(row.get("f171",None)),
            clean_numeric(row.get("f172",None)),
            clean_numeric(row.get("f173",None)),

            clean_numeric(row.get("f160", None)),
            clean_numeric(row.get("f174",None)),
            clean_numeric(row.get("f175",None)),
            clean_numeric(row.get("f176",None)),
            clean_numeric(row.get("f177",None)),
            clean_numeric(row.get("f178",None)),
            clean_numeric(row.get("f179",None)),
            clean_numeric(row.get("f180",None)),
            clean_numeric(row.get("f181",None)),
            clean_numeric(row.get("f182",None)),
            clean_numeric(row.get("f183",None)),
            '2025-12-30'

        )
        for row in rows
    ]
    with conn.cursor() as cursor:
        cursor.executemany(STOCK_SQL, values)
        conn.commit()

def clean_numeric(value, default=0.0):
    """清洗数值字段"""
    if value in ('-', '', None):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def main():
    """主函数：整合所有板块数据并导出Excel"""
    all_results = []
    # 遍历所有板块类型（行业/概念/地域）
    for board_type, filter_param in BOARD_TYPES.items():
        print(f"\n开始抓取【{board_type}】数据...")
        boards = get_board_list(filter_param)
        if not boards:
            print(f"未获取到{board_type}的板块数据")
            continue

        # 逐个获取每个板块的市值最大公司
        for idx, (board_name, board_code) in enumerate(boards, 1):
            get_top_market_cap_company(board_code,board_name)
    conn.close()
    #         all_results.append({
    #             '板块类型': board_type,
    #             '板块名称': board_name,
    #             '市值最大公司': top_company
    #         })
    #         print(f"进度：{idx}/{len(boards)} | {board_type} - {board_name}：{top_company}")
    #
    # # 将数据写入Excel
    # if all_results:
    #     df = pd.DataFrame(all_results)
    #     # 导出Excel，指定引擎避免格式问题
    #     df.to_excel('东方财富各板块市值最大公司.xlsx', index=False, engine='openpyxl')
    #     print("\n✅ 数据已成功导出到「东方财富各板块市值最大公司.xlsx」")
    # else:
    #     print("\n❌ 未获取到任何板块数据，无法生成Excel")


if __name__ == '__main__':
    main()