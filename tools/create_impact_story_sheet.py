# -*- coding: utf-8 -*-
"""
create_impact_story_sheet.py
インパクト強め版：意外性・強烈フック・感情の落差を重視したストーリー構成
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from google.oauth2 import service_account
from googleapiclient.discovery import build

SHEET_ID = "1vBVvQZ-3p0vz8rQAQye8L-0AvmUiuuxW929ZV3PyRgM"
NEW_SHEET = "インパクト版ストーリー"

creds = service_account.Credentials.from_service_account_file(
    "credentials/google_service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
service = build("sheets", "v4", credentials=creds)

meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
for s in meta["sheets"]:
    if s["properties"]["title"] == NEW_SHEET:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": [{"deleteSheet": {"sheetId": s["properties"]["sheetId"]}}]},
        ).execute()

resp = service.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={"requests": [{"addSheet": {"properties": {"title": NEW_SHEET}}}]},
).execute()
new_sheet_id = resp["replies"][0]["addSheet"]["properties"]["sheetId"]
print("new sheet id:", new_sheet_id)

result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range="動画構成パターン"
).execute()
rows = result.get("values", [])
header = rows[0]
data = rows[1:]

def get(row, col_name):
    idx = header.index(col_name) if col_name in header else -1
    if idx == -1 or idx >= len(row): return ""
    return row[idx].strip()

patterns = {}
order = []
current_product = ""
for row in data:
    product = get(row, "商品グループ")
    if product: current_product = product.replace("\n", " ")
    category = get(row, "カテゴリー").replace("\n", " ")
    key = category
    if key not in patterns:
        patterns[key] = {
            "product": current_product, "category": category,
            "appeal": get(row, "訴求軸"), "duration": get(row, "推奨尺"),
            "format": get(row, "投稿形式"),
            "influencer": get(row, "参考インフルエンサー").replace("\n", " / "),
        }
        order.append(key)
    if not patterns[key]["influencer"] and get(row, "参考インフルエンサー"):
        patterns[key]["influencer"] = get(row, "参考インフルエンサー").replace("\n", " / ")

# インパクト強め版ストーリー（強烈フック・意外性・感情の落差）
impact_stories = {
    "1 PPSU素材・安全性": (
        "①\n"
        "赤ちゃんに毒を飲ませてたかもしれない。\n"
        "強い言い方だけど、これ本当のことなので聞いてほしい。\n\n"
        "②\n"
        "PP素材のマグ、使ってる人いるよね。\n"
        "高温で繰り返し洗うたびに、肉眼では見えないレベルで\n"
        "少しずつ劣化して溶け出していく。\n\n"
        "③\n"
        "その劣化した素材がお茶やお湯に溶けて\n"
        "赤ちゃんが毎日飲んでいる。これが現実。\n\n"
        "④\n"
        "PPSUはレベルが全然違う。\n"
        "医療現場で哺乳瓶に使われる素材、\n"
        "最高温140度でも変質しない。\n\n"
        "⑤\n"
        "「でも高いんでしょ？」と思った。\n"
        "正直に言う。安いマグで赤ちゃんの健康をリスクにさらすか、\n"
        "安全な素材に投資するか。その選択だと思ってる。\n\n"
        "⑥\n"
        "赤ちゃんは自分で選べない。\n"
        "それだけが、私が素材にこだわる理由。"
    ),
    "2 漏れない": (
        "①\n"
        "漏れるのはマグのせいじゃない、かもしれない。\n\n"
        "②\n"
        "「逆止弁がないストロー」は\n"
        "構造上、必ず漏れる。\n"
        "どんな密閉容器でもストローが入ってる以上\n"
        "漏れるリスクとセットだと思っていい。\n\n"
        "③\n"
        "グロスミミの+CUTストローは逆止弁内蔵。\n"
        "逆さにしても液体が逆流しない。\n\n"
        "④\n"
        "実証する。\n"
        "逆さにしても → 漏れない\n"
        "グリグリ振っても → 漏れない\n"
        "全力で投げても → 漏れない\n\n"
        "⑤\n"
        "「そんなわけない」と思った人、\n"
        "一度やってみてほしい。本当に漏れないから。\n\n"
        "⑥\n"
        "漏れるのが当たり前だと思ってた過去の自分へ。\n"
        "当たり前じゃなかった。"
    ),
    "3 離乳食期に使える": (
        "①\n"
        "離乳食のパウチにストローマグが刺さるって\n"
        "なんでどのメーカーもやってないの？\n\n"
        "②\n"
        "外出先で離乳食パウチ + マグ + 水筒きり\n"
        "荷物が多すぎる問題、全員が抱えてると思う。\n"
        "誰もこれを解決しようとしてなかった。\n\n"
        "③\n"
        "グロスミミのマグ、パウチの元口にそのまま刺せる。\n"
        "先端が小さくて隙間なく収まる。\n\n"
        "④\n"
        "外出先の離乳食がマグで飲み物になる。\n"
        "荷物が値段分減る。\n"
        "これ知ってる人少なすぎる。\n\n"
        "⑤\n"
        "離乳食が始まったばかりのママへ。\n"
        "マグだけでそのストレス、少し減らせるかもしれない。"
    ),
    "4 ストロー練習": (
        "①\n"
        "ストロー練習、教えるのはママじゃない。\n"
        "道具が教える。\n\n"
        "②\n"
        "吸わせて教えて、くれてやって、\n"
        "それでも飲めなかったのに\n"
        "マグ変えただけで飲めた。\n\n"
        "③\n"
        "（動画：失敗）\n"
        "↓\n"
        "（動画：同じ日に成功）\n\n"
        "④\n"
        "なぜか。ストローの硬さと長さ。\n"
        "赤ちゃんの口の大きさと流量に合わせて設計されてるから\n"
        "自然と吸い方を体が覚える。\n\n"
        "⑤\n"
        "「その子が来た」と思ってたら\n"
        "実は道具が正しくなかっただけかもしれない。\n\n"
        "⑥\n"
        "ストロー練習中のママ、\n"
        "マグをリセットする前に一度封を開けてみてほしい。"
    ),
    "5 医療グレードステンレス (保温保冷)": (
        "①\n"
        "100円均一のステンレスと\n"
        "医療グレードステンレス、\n"
        "同じ「ステンレス」と書いてある。\n\n"
        "②\n"
        "SUS201（均一品）→ ニッケル溶出リスクあり\n"
        "SUS304（一般品）→ 一般的な飲料容器レベル\n"
        "SUS316（医療器具・手術器具レベル）→ グロスミミ\n\n"
        "③\n"
        "「全部同じでしょ」と思うなら\n"
        "手術器具と100均の金属が\n"
        "同じだと思いますか？\n\n"
        "④\n"
        "内側が一番大事。\n"
        "口に触れる面が医療グレードかどうか。\n"
        "保温6時間はおまけ。\n\n"
        "⑤\n"
        "ステンレスマグを選ぶなら\n"
        "内側のグレードだけは確認してほしい。\n"
        "それだけで選択が変わる。"
    ),
    "6 漏れない (保温x漏れない両立)": (
        "①\n"
        "「ホットは危ないから冷たいのしか入れない」\n"
        "この思い込み、全部のママが持ってると思う。\n\n"
        "②\n"
        "グロスミミのステンレスマグに\n"
        "熱湯を入れてテーブルから落とす。\n"
        "漏れない。\n\n"
        "③\n"
        "倒す。振る。投げる。\n"
        "全部OK。ホット入れたまま。\n\n"
        "④\n"
        "保温6時間と漏れない構造を\n"
        "同時に持てるマグがこれまでなかった。\n"
        "冬の外出、これで変わる。\n\n"
        "⑤\n"
        "ホットのこぼれ、もう気にしなくていい。\n"
        "それだけでお出かけの心理的な重さが減る。"
    ),
    "7 つなぎ目なし (シームレス)": (
        "①\n"
        "毎日洗ってるのに\n"
        "洗えてない部分がある。\n\n"
        "②\n"
        "溶接の継ぎ目。髪の毛より細い溝。\n"
        "スポンジは届かない。\n"
        "そこに汚れとカビが溜まっていく。\n\n"
        "③\n"
        "「洗った」という安心感で\n"
        "毎日その汚れを子どもの口に入れ続けてるかもしれない。\n\n"
        "④\n"
        "シームレス構造は溝がそもそも存在しない。\n"
        "洗えない場所が最初からない。\n\n"
        "⑤\n"
        "清潔に自信がある人ほど、\n"
        "一度マグの内側を確認してほしい。\n"
        "継ぎ目があるかどうか。それだけ。\n\n"
        "⑥\n"
        "洗っても洗っても気になる人へ。\n"
        "気になるのはあなたのせいじゃないかもしれない。"
    ),
    "8 比較・買い替え訴求": (
        "①\n"
        "最初に買ったマグを今も使ってる人へ。\n"
        "赤ちゃんの口に入るもの、\n"
        "後で後悔するだけじゃないの？\n\n"
        "②\n"
        "一軍のマグ：漏れる、匂いつく、内側が洗いにくい\n"
        "グロスミミ：漏れない、匂わない、内側シームレス\n"
        "比べるのがおかしいくらい差がある。\n\n"
        "③\n"
        "「どうせマグなんて同じ」と思ってた自分へ。\n"
        "全然同じじゃなかった。\n\n"
        "④\n"
        "第二子が生まれる前に\n"
        "この事実を知れてよかった。\n\n"
        "⑤\n"
        "買い替えを迷ってる人へ。\n"
        "迷ったまま使い続ける方が消費が大きいかもしれない。\n\n"
        "⑥\n"
        "一度良いものを使うと\n"
        "元に戻れなくなる。それが良い道具の恋しさ。"
    ),
    "9 夏・暖かい季節 保冷・衛生訴求": (
        "①\n"
        "気温が5度上がると\n"
        "マグの麦茶が腐るまでの時間、半分以下になる。\n"
        "これ知ってた？\n\n"
        "②\n"
        "子どもが昼寝してる間に\n"
        "マグの中の麦茶が腐っている。\n"
        "暗黙のうちに起きてること。\n\n"
        "③\n"
        "保冷6時間で4度以下を維持するマグは\n"
        "それを構造的に防ぐ。\n"
        "温度管理は衛生管理。\n\n"
        "④\n"
        "しかも内側シームレスで\n"
        "継ぎ目のカビ・汚れが溜まらない。\n"
        "夜サッと洗えるだけ。\n\n"
        "⑤\n"
        "夏の外出でお茶を持たせるのが怖くなる前に。\n"
        "マグ一本でその不安、構造的に潰せる。"
    ),
    "10 ストロー構造メイン": (
        "①\n"
        "ストローマグを買って「ストローが臭い」と言う人へ。\n"
        "それ、ストローの責任じゃない、かもしれない。\n\n"
        "②\n"
        "一般的なストローの欠陥：\n"
        "内部に液体が逆流して残る → 菌が繁殖 → 臭う\n"
        "毎日洗っても追いつかない理由がここにある。\n\n"
        "③\n"
        "+CUTストローの逆止弁は\n"
        "液体の逆流を構造上ゼロにする。\n"
        "残る液体がない → 菌が繁殖しない → 臭わない。\n\n"
        "④\n"
        "全パーツ分解で食洗機OK。\n"
        "ストローだけの交換もできる。\n"
        "本体を捨てなくていい。\n\n"
        "⑤\n"
        "ストローマグで後悔する前に、\n"
        "ストロー自体の構造を一度確認してほしい。\n"
        "側面じゃなく、内部の仕組みを。"
    ),
}

impact_points = {
    "1 PPSU素材・安全性":        "💥「毒を飲ませてたかも」— 親の罪悪感に点火する強烈フック",
    "2 漏れない":                "💥「漏れるのは構造上当たり前」— 常識の否定から入る",
    "3 離乳食期に使える":        "💥「なんでどのメーカーもやってないの？」— 純粋な疑問が最強フック",
    "4 ストロー練習":            "💥「教えるのは道具である」— ママの努力を否定する逆説",
    "5 医療グレードステンレス (保温保冷)": "💥「手術器具と100均が同じ素材？」— スケールのギャップで信頼を崩す",
    "6 漏れない (保温x漏れない両立)": "💥「ホットは危ない」思い込みをぶち壊す実証",
    "7 つなぎ目なし (シームレス)": "💥「洗ってるのに洗えてない」— 清潔への自信を静かに崩す",
    "8 比較・買い替え訴求":      "💥「後悔するだけじゃないの？」— 直接的な問いかけで行動を迫る",
    "9 夏・暖かい季節 保冷・衛生訴求": "💥「気温+5度で腐る時間が半分」— 数字で不安を具体化する",
    "10 ストロー構造メイン":     "💥「臭いのはストローの責任じゃない」— 責任の矛先を反転させる",
}

output = []
output.append([
    "商品グループ", "カテゴリー", "訴求タイプ", "投稿形式", "推奨尺",
    "💥 インパクトの核心（なぜ止まるか）",
    "ストーリー（インパクト強め・意外性重視）",
    "参考インフルエンサー",
])

for key in order:
    p = patterns[key]
    output.append([
        p["product"], p["category"], p["appeal"], p["format"], p["duration"],
        impact_points.get(p["category"], ""),
        impact_stories.get(p["category"], ""),
        p["influencer"],
    ])

service.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range=f"{NEW_SHEET}!A1",
    valueInputOption="RAW", body={"values": output},
).execute()
print(f"write done: {len(output)-1} patterns")

requests = []
requests.append({
    "repeatCell": {
        "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 0.1, "green": 0.05, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP",
        }},
        "fields": "userEnteredFormat",
    }
})
requests.append({
    "repeatCell": {
        "range": {"sheetId": new_sheet_id, "startRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 1.0, "green": 0.85, "blue": 0.85},
            "textFormat": {"bold": True},
            "wrapStrategy": "WRAP", "verticalAlignment": "TOP",
        }},
        "fields": "userEnteredFormat",
    }
})
requests.append({
    "repeatCell": {
        "range": {"sheetId": new_sheet_id, "startRowIndex": 1},
        "cell": {"userEnteredFormat": {
            "wrapStrategy": "WRAP", "verticalAlignment": "TOP",
            "textFormat": {"fontSize": 9},
        }},
        "fields": "userEnteredFormat",
    }
})
for i, w in enumerate([150, 180, 140, 100, 80, 280, 400, 160]):
    requests.append({
        "updateDimensionProperties": {
            "range": {"sheetId": new_sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i+1},
            "properties": {"pixelSize": w}, "fields": "pixelSize",
        }
    })
requests.append({
    "updateDimensionProperties": {
        "range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 36}, "fields": "pixelSize",
    }
})
requests.append({
    "updateDimensionProperties": {
        "range": {"sheetId": new_sheet_id, "dimension": "ROWS", "startIndex": 1},
        "properties": {"pixelSize": 280}, "fields": "pixelSize",
    }
})
requests.append({
    "updateBorders": {
        "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": len(output), "startColumnIndex": 0, "endColumnIndex": 8},
        "top": {"style": "SOLID", "width": 1}, "bottom": {"style": "SOLID", "width": 1},
        "left": {"style": "SOLID", "width": 1}, "right": {"style": "SOLID", "width": 1},
        "innerHorizontal": {"style": "SOLID", "width": 1}, "innerVertical": {"style": "SOLID", "width": 1},
    }
})
requests.append({
    "updateSheetProperties": {
        "properties": {"sheetId": new_sheet_id, "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount",
    }
})
service.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": requests}).execute()
print("format done")
print(f"URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={new_sheet_id}")
