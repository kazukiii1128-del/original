# -*- coding: utf-8 -*-
"""
create_b2b_list_sheet.py
グロミミ B2B リスト（ベビー専門 50社）を Google Spreadsheet に出力する
列: カテゴリ / # / 社名 / 規模 / 主要エリア / 本社 / TEL / 卸・問合せ先 / 公式URL / 情報ソース / SNS / 担当者情報 / アプローチメモ
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    "credentials/google_service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
svc = build("sheets", "v4", credentials=creds)

SHEET_ID   = "1wAtotUgxyaUP4C-JTGMyDPurjfv5QC_q9N8l9M8nafE"
SHEET_NAME = "B2Bリスト"
print(f"Using: {SHEET_ID}")

# ── シート再作成 ─────────────────────────────────────────────────────────────
meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
old_id = next((s["properties"]["sheetId"] for s in meta["sheets"]
               if s["properties"]["title"] == SHEET_NAME), None)

batch = [{"addSheet": {"properties": {"title": SHEET_NAME + "_new"}}}]
if old_id is not None:
    batch.append({"deleteSheet": {"sheetId": old_id}})
r = svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": batch}).execute()
sheet_id = r["replies"][0]["addSheet"]["properties"]["sheetId"]
svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": [
    {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "title": SHEET_NAME},
                               "fields": "title"}}
]}).execute()
print(f"Sheet ready (id={sheet_id})")

# ── ヘッダー ─────────────────────────────────────────────────────────────────
H = ["カテゴリ","#","社名","規模・店舗数","主要エリア",
     "本社所在地","電話番号","卸・問い合わせ先","公式URL",
     "情報ソース（どこで調べたか）","SNSアカウント","担当者情報","アプローチメモ"]

# ── データ 40社 ───────────────────────────────────────────────────────────────
# 列順: カテゴリ, #, 社名, 規模, エリア, 本社, TEL, 卸/問合, URL, ソース, SNS, 担当者, アプローチ
rows = [

# ===== A. 大手ベビー専門チェーン =====
["A. 大手ベビー専門チェーン","1",
 "株式会社赤ちゃん本舗（アカチャンホンポ）",
 "129店舗・売上830億円・従業員3,838名",
 "全国（本社：大阪）",
 "〒541-0054 大阪府大阪市中央区南本町3-3-21",
 "06-6251-0625（代表）",
 "https://www.akachan.jp/company/（問合せフォームあり）",
 "https://www.akachan.jp/",
 "akachan.jp/company/about/outline/ ／ LinkedIn（土師弘明・マーケティング役員）",
 "Instagram: @akachan_jp ／ X: @AkachanHonpo",
 "マーケティング担当役員: 土師弘明（LinkedIn確認）\nバイヤー（授乳・離乳）: 池内佐智（採用ページ記載）",
 "取引先募集フォームまたは展示会。担当役員にLinkedInからコンタクト可"],

["A. 大手ベビー専門チェーン","2",
 "株式会社西松屋チェーン",
 "1,153店舗・東証プライム上場",
 "全国（本社：兵庫/姫路）",
 "兵庫県姫路市飾東町庄266番地",
 "079-252-3300（本社）",
 "https://www.24028.jp/contact/（問合せフォーム）",
 "https://www.24028.jp/",
 "24028.jp/company/outline ／ Wikipedia",
 "Instagram: @nishimatsuya_official ／ X: @nishimatsuya",
 "海外向け卸販売ページあり（24028.jp/global/en/）",
 "海外卸窓口あり。国内は展示会・商談会経由が一般的"],

["A. 大手ベビー専門チェーン","3",
 "日本トイザらス株式会社（ベビーザらス）",
 "約150店舗・代表取締役社長: 李孝",
 "全国（本社：神奈川/川崎）",
 "神奈川県川崎市幸区大宮町1310番地 ミューザ川崎25F",
 "",
 "info@mail.toysrusonline.co.jp",
 "https://www.babiesrus.co.jp/",
 "toysrus.co.jp/ja-jp/corporate-about.html ／ LinkedIn公式ページあり",
 "Instagram: @babiesrus_jp ／ X: @TOYSRUS_JP ／ LinkedIn: 日本トイザらス株式会社",
 "代表取締役社長: 李孝 ／ LinkedIn: jp.linkedin.com/company/日本トイザらス株式会社",
 "アップリカ・コンビの専門コーナー導入実績あり。展示会・LinkedInでアプローチ"],

["A. 大手ベビー専門チェーン","4",
 "株式会社しまむら（バースデイ）",
 "バースデイ約300店舗・グループ2,200店以上",
 "全国（本社：埼玉/さいたま）",
 "〒330-0854 埼玉県さいたま市大宮区桜木町1-7-5",
 "048-600-8800",
 "https://www.shimamura.gr.jp/contact/",
 "https://www.s-birthday.com/",
 "s-birthday.com ／ diamond-rm.net（店舗数情報）",
 "Instagram: @grbirthday ／ X: @birthday_gr",
 "取引先担当はしまむら本社商品部。個人名は非公開",
 "コスパ重視・ベビー用品約7万点取扱。展示会でのアプローチ推奨"],

["A. 大手ベビー専門チェーン","5",
 "株式会社ハロー赤ちゃん",
 "9店舗（東海・近畿・関東）",
 "東海中心（本社：愛知/岡崎）",
 "愛知県岡崎市",
 "",
 "https://www.hello-akachan.co.jp/contact/",
 "https://www.hello-akachan.co.jp/",
 "hello-akachan.co.jp/company/profile/ ／ Baseconnect",
 "Instagram: @helloakachan_official（5,454フォロワー）\nFacebook: facebook.com/helloakachan860/",
 "代表取締役: 木戸口勤 ／ 創業85年",
 "イオンモール内出店多数。InstagramかFacebook経由で担当者に接触可"],

["A. 大手ベビー専門チェーン","6",
 "株式会社赤ちゃんデパート水谷",
 "18店舗・従業員233名",
 "東海中心（本社：愛知/蟹江町）",
 "〒497-0058 愛知県海部郡蟹江町富吉三丁目246番地",
 "",
 "https://akadepamizutani.net/contact/",
 "https://akadepamizutani.net/",
 "akadepamizutani.net/company/ ／ Wikipedia",
 "Instagram: @akadepamizutani_official（16K フォロワー）\nThreads: @akadepamizutani_official",
 "代表取締役: 水谷明 ／ 資本金1,000万円",
 "地域密着型。InstagramDMまたは問い合わせフォーム経由が有効"],

# ===== B. 百貨店（ベビー売場） =====
["B. 百貨店（ベビー売場）","7",
 "イオン（キッズリパブリック）",
 "全国イオングループ展開",
 "全国（本社：千葉）",
 "〒261-8515 千葉県千葉市美浜区中瀬1-5-1",
 "043-212-6300",
 "https://www.kidsrepublic.jp/contact/",
 "https://www.kidsrepublic.jp/",
 "kidsrepublic.jp ／ aeon.com",
 "Instagram: @kidsrepublic_jp ／ X: @kidsrepublic_jp",
 "イオン本社MD部門への商談が必要。担当部署は子育て事業部",
 "ベビー・キッズ専門コーナー。イオン商品説明会経由でのアプローチ"],

["B. 百貨店（ベビー売場）","8",
 "株式会社高島屋",
 "国内17店舗・東証プライム上場",
 "全国（本社：大阪）",
 "〒542-8510 大阪府大阪市中央区難波5-1-5",
 "06-6631-1101",
 "https://www.takashimaya.co.jp/base/corp/contact/",
 "https://www.takashimaya.co.jp/shopping/baby/",
 "takashimaya.co.jp/shopping/baby/ ／ Wikipedia",
 "X: @takashimaya_jp ／ Instagram: @takashimaya_official",
 "ベビー・キッズバイヤーは各店舗MD担当。ファミリア等の取扱実績あり",
 "ブランド認知向上に直結。新宿/日本橋/大阪のMD担当へのアプローチ推奨"],

["B. 百貨店（ベビー売場）","9",
 "三越伊勢丹ホールディングス",
 "国内12店舗・東証プライム上場",
 "全国（本社：東京）",
 "〒160-0022 東京都新宿区新宿3-14-1",
 "03-3352-1111",
 "https://www.mistore.jp/contact/",
 "https://www.mistore.jp/shopping/brand/baby_kids_b/",
 "mistore.jp ／ Wikipedia ／ LinkedIn（三越伊勢丹）",
 "Instagram: @mistore_official ／ X: @mistore_jp",
 "familiar・MARLMARL等の取扱実績あり。LinkedIn上で社員多数確認可",
 "高感度層向け。伊勢丹新宿のMD担当へのアプローチ推奨。LinkedInでバイヤー検索可"],

["B. 百貨店（ベビー売場）","10",
 "阪急阪神百貨店（エイチ・ツー・オー リテイリング）",
 "関西主要店舗",
 "関西中心（本社：大阪）",
 "〒530-8350 大阪府大阪市北区角田町8-7",
 "06-6361-1381",
 "",
 "https://www.hankyu-dept.co.jp/",
 "hankyu-dept.co.jp ／ ミキハウス・10moisの取扱実績（10mois公式サイト）",
 "Instagram: @hankyu_dept ／ X: @hankyu_dept",
 "ミキハウス・10moisの取扱実績あり。うめだ本店がフラッグシップ",
 "関西圏の高感度層に強み。博多阪急のベビー売場も有力"],

["B. 百貨店（ベビー売場）","11",
 "大丸松坂屋百貨店（株式会社J.フロントリテイリング）",
 "全国18店舗・東証プライム上場",
 "全国（東京・大阪中心）",
 "〒135-8711 東京都江東区木場2-18-11",
 "03-6895-0001",
 "",
 "https://www.daimaru.co.jp/",
 "daimaru.co.jp ／ matsuzakaya.co.jp",
 "Instagram: @daimaru_matsuzakaya ／ X: @daimaru_info",
 "百貨店ベビー売場。担当バイヤーは各店MD部門",
 "大丸東京・松坂屋名古屋のMD担当へのアプローチ"],

# ===== C. セレクトショップ・ブランドショップ =====
["C. セレクトショップ","12",
 "blossom39（株式会社azas）",
 "全国20店舗以上・代表: 河野さくら",
 "全国（本社：東京/渋谷）",
 "東京都渋谷区猿楽町9-8",
 "03-5459-3914（卸売担当）",
 "wholesale@azas.jp（卸売専用）",
 "https://www.blossom39.com/",
 "blossom39.com/pages/wholesaler ／ blossom39.com/pages/company",
 "Instagram: @blossom39_official ／ Facebook: facebook.com/blossom39/",
 "代表取締役: 河野さくら ／ 卸売担当窓口あり",
 "卸売専用フォーム・メール・TELあり。グロミミと親和性最高。即アプローチ可"],

["C. セレクトショップ","13",
 "株式会社ファミリア",
 "全国73店舗（百貨店内中心）",
 "全国（本社：兵庫/神戸）",
 "〒651-0086 神戸市中央区磯上通4-3-10",
 "078-291-4567（代表）",
 "https://familiar.co.jp/pages/company2（問合せ）",
 "https://familiar.co.jp/",
 "familiar.co.jp/pages/company2 ／ fashion-press.net",
 "Instagram: @familiar_official ／ Facebook: familiar.co.jp",
 "代表取締役社長: 岡崎忠彦 ／ 東京オフィス: 六本木ヒルズ3F",
 "神戸発の老舗ブランド。東京オフィスへのアプローチが近道"],

["C. セレクトショップ","14",
 "こどもビームス（株式会社ビームス）",
 "全国ビームス店舗内",
 "全国（本社：東京/渋谷）",
 "〒150-0001 東京都渋谷区神宮前3-24-7",
 "03-3470-3951",
 "",
 "https://www.beams.co.jp/en/brand/000023/",
 "beams.co.jp ／ beams公式サイト",
 "Instagram: @beams_official ／ X: @BEAMS_PR",
 "ビームス本社MDに商談申請。担当バイヤーはキッズ部門",
 "トレンド感強め。ビームス本社へのアプローチでキッズMD担当に繋ぐ"],

["C. セレクトショップ","15",
 "10mois（有限会社Ficelle）",
 "全国直営8店舗＋百貨店取扱多数",
 "全国（本社：愛知）",
 "愛知県豊川市",
 "0533-65-8255",
 "10moisinfo@ficelle.co.jp",
 "https://10mois.com/",
 "10mois.com/pages/会社概要 ／ ficelle.co.jp",
 "Instagram: @10mois_official（96K フォロワー）\nFacebook: facebook.com/ficelle.inc/",
 "セレクト仕入れ実績あり。問い合わせメール窓口あり",
 "セレクト仕入れ窓口あり。メール・Instagram DMでアプローチ可"],

["C. セレクトショップ","16",
 "VIRINA（ヴィリーナ）",
 "オンライン＋一部実店舗",
 "東京中心",
 "東京都",
 "",
 "https://www.virinamaternity.com/contact/",
 "https://www.virinamaternity.com/",
 "virinamaternity.com ／ carryonmall.com",
 "Instagram: @virina_official",
 "マタニティ・ベビーのセレクトショップ",
 "感度の高いママ層に支持。Instagram DM経由でのアプローチが有効"],

["C. セレクトショップ","17",
 "銀座いさみや",
 "1店舗（銀座三越隣）",
 "東京（銀座）",
 "東京都中央区銀座",
 "",
 "https://www.ginza-isamiya.com/contact/",
 "https://www.ginza-isamiya.com/",
 "ginza-isamiya.com ／ WebSearch調査",
 "Instagram: @ginza_isamiya",
 "日本製ベビー用品のみ取扱。こだわりのセレクト",
 "高感度・高価格帯。Made in Japan重視。問い合わせフォームでアプローチ"],

["C. セレクトショップ","18",
 "BabyGoose（株式会社グースカンパニー）",
 "1店舗（白金台）＋EC",
 "東京（港区白金台）",
 "〒108-0071 東京都港区白金台5-10-10-1F",
 "03-3280-5192",
 "order@babygoose.jp",
 "https://www.babygoose.jp/",
 "goosecompany.com ／ prtimes.jp（創業40周年PR）",
 "Instagram: @babygoose_jp ／ Facebook: BabyGoose.Japan",
 "代表: 千葉宏一 ／ キッズデザイン賞4年連続受賞",
 "名入れ出産祝い専門。コラボ提案・卸交渉ともにメール窓口あり"],

["C. セレクトショップ","19",
 "MARLMARL（株式会社Yom）",
 "EC中心＋百貨店（三越伊勢丹）取扱",
 "東京（渋谷）",
 "東京都渋谷区",
 "",
 "https://www.marlmarl.com/contact/",
 "https://www.marlmarl.com/",
 "marlmarl.com ／ mistore.jp（三越取扱確認）／ Wikipedia",
 "Instagram: @marlmarl_tokyo（130K フォロワー）\n@mato_by_marlmarl ／ @studio_marlmarl",
 "三越伊勢丹・blossom39での取扱実績あり",
 "出産祝いギフト需要。Instagram DM or 問い合わせフォームでアプローチ可"],

["C. セレクトショップ","20",
 "株式会社ダッドウェイ",
 "従業員209名・輸入代理＋卸売",
 "全国（本社：神奈川/横浜）",
 "〒222-0033 神奈川県横浜市港北区新横浜2-15-12",
 "0120-880-188",
 "https://www.dadway.com/contact/",
 "https://www.dadway.com/",
 "dadway.com/company/outline/ ／ prtimes.jp（社長就任PR）",
 "Instagram: @dadway（47K フォロワー）\n@dadway_store_official（11K）",
 "代表取締役社長: 大野浩人 ／ エルゴベビー・スキップホップ等の輸入代理店",
 "赤ちゃん本舗・イオン等への卸実績多数。取引相談は問い合わせフォームから"],

["C. セレクトショップ","21",
 "三起商行株式会社（ミキハウス）",
 "国内約90店舗・世界108店舗",
 "全国（本社：大阪/八尾）",
 "〒581-8580 大阪府八尾市若林町1-76-2",
 "0120-891-079（お客様専用）",
 "https://www.mikihouse.co.jp/pages/corporate-contact",
 "https://www.mikihouse.co.jp/",
 "mikihouse.co.jp/pages/corporate-company-information ／ Wikipedia",
 "Instagram: @mikihouse_official ／ X: @MIKIHOUSE_PR",
 "代表取締役: 木村皓一 ／ 資本金2,030百万円",
 "プレミアムベビーブランド。取引相談は企業コンタクトフォームから"],

["C. セレクトショップ","22",
 "株式会社ナルミヤ・インターナショナル",
 "全国151店舗（SC内中心）・東証スタンダード上場",
 "全国（本社：東京/港区）",
 "〒105-0011 東京都港区芝公園2-4-1",
 "",
 "https://www.narumiya-net.co.jp/corporate/company/",
 "https://www.narumiya-net.co.jp/",
 "narumiya-net.co.jp/corporate/company/ ／ Wikipedia",
 "Instagram: @petitmain_official（プティマイン）",
 "株式会社ワールドの子会社 ／ petit main・mezzo pianoを展開",
 "SC内ベビー・キッズブランド。ワールドグループへの商談申請"],

# ===== D. EC・通販 =====
["D. EC・通販","23",
 "ベルメゾンネット（株式会社千趣会）",
 "カタログ通販大手",
 "全国（本社：大阪）",
 "〒530-8566 大阪府大阪市北区同心2-6-48",
 "06-6357-1100",
 "https://www.bellemaison.jp/contact/",
 "https://www.bellemaison.jp/shop/app/catalog/category_top/5/",
 "bellemaison.jp ／ Wikipedia",
 "Instagram: @bellemaison_official ／ X: @BelleMaison",
 "カタログ通販。ベビー・マタニティ部門への商談窓口あり",
 "カタログ掲載交渉が有効。掲載実績がブランド認知に繋がる"],

["D. EC・通販","24",
 "コンビミニ（河和紡株式会社）",
 "EC中心（ZOZO・楽天等にも出店）",
 "全国（EC）",
 "東京都",
 "",
 "",
 "https://www.combimini.com/",
 "combimini.com ／ zozo.jp（取扱確認）",
 "Instagram: @combimini_official",
 "コンビブランドのベビー服専門EC（2024年よりブランド移管）",
 "協業・タイアップ余地あり。問い合わせフォームからアプローチ"],

["D. EC・通販","25",
 "ナイスベビー",
 "レンタル＋販売EC",
 "全国（EC）",
 "東京都",
 "",
 "https://www.nicebaby.co.jp/pages/contact",
 "https://www.nicebaby.co.jp/",
 "nicebaby.co.jp/pages/about",
 "Instagram: @nicebaby_official",
 "レンタル→購入転換モデル。試用できるチャネル",
 "レンタル経由でのブランド体験→購買導線。タイアップ交渉可"],

# ===== E. 小規模・輸入系セレクトショップ =====
["E. 小規模セレクトショップ","26",
 "OBEBE（おべべ）",
 "オンライン中心",
 "全国（EC）",
 "","","",
 "https://shop.obebe.co.jp/",
 "shop.obebe.co.jp ／ WebSearch（Konges Sloejd取扱確認）",
 "Instagram: @obebe_shop",
 "北欧・輸入ベビー服セレクト",
 "Instagram DM または公式ECのお問い合わせフォームからアプローチ"],

["E. 小規模セレクトショップ","27",
 "INSPIREme",
 "オンライン中心",
 "全国（EC）",
 "","","",
 "https://inspireme.jp/",
 "inspireme.jp ／ WebSearch",
 "Instagram: @inspireme_jp",
 "輸入子供服通販セレクトショップ",
 "Instagramまたは問い合わせフォームからアプローチ"],

["E. 小規模セレクトショップ","28",
 "LILI et NENE（リリエネネ）",
 "オンライン中心",
 "全国（EC）",
 "","","",
 "https://www.lilietnene.com/",
 "lilietnene.com ／ WebSearch（Konges Sloejd正規販売確認）",
 "Instagram: @lilietnene_official",
 "パリ・北欧輸入ベビー服。Konges Sloejd正規販売",
 "Instagram DM または問い合わせフォームでアプローチ"],

["E. 小規模セレクトショップ","29",
 "Little Lemonade Days",
 "京都実店舗＋EC",
 "関西（京都）",
 "京都府","","",
 "https://ll-days.com/",
 "ll-days.com ／ WebSearch（Konges Sloejd輸入・取扱確認）",
 "Instagram: @littlelemonadedays",
 "北欧ベビー服輸入・セレクト。実店舗あり",
 "Instagram DM または実店舗へのアプローチが有効"],

["E. 小規模セレクトショップ","30",
 "KIDSMIO",
 "オンライン・卸対応",
 "全国（EC）",
 "","","",
 "https://www.kidsmio.com/",
 "kidsmio.com ／ WebSearch（卸対応確認）",
 "Instagram: @kidsmio",
 "ベビー・キッズ輸入・卸販売対応",
 "卸対応あり。ネットショップ・実店舗向け卸交渉可"],

["E. 小規模セレクトショップ","31",
 "Sweet Mommy（スウィートマミー）",
 "EC中心",
 "全国（EC）",
 "東京都","","",
 "https://www.sweetmommy.com/",
 "sweetmommy.com ／ rakuten.co.jp（楽天出店確認）",
 "Instagram: @sweetmommyofficial",
 "マタニティ・授乳服・ベビー服専門EC",
 "感度の高いママ層に支持。Instagram DM or 問い合わせフォーム"],

["E. 小規模セレクトショップ","32",
 "Angeliebe（エンジェリーベ）/ 丸子株式会社",
 "EC中心",
 "全国（EC）",
 "","","",
 "https://www.angeliebe.co.jp/",
 "angeliebe.co.jp/help/company",
 "Instagram: @angeliebe_official",
 "丸子株式会社が運営するマタニティ・授乳服通販",
 "妊娠〜育児期のママ層に特化。問い合わせフォームからアプローチ"],

["E. 小規模セレクトショップ","33",
 "ブリリアントベビー（BrilliantBaby）",
 "EC中心",
 "全国（EC）",
 "","","",
 "https://bribaby.jp/",
 "bribaby.jp ／ WebSearch（セレクトショップ確認）",
 "Instagram: @brilliantbaby_jp",
 "ベビー用品セレクトショップ",
 "問い合わせフォームまたはInstagram DM"],

# ===== F. 卸売・ディストリビューター =====
["F. 卸売・ディストリビューター","34",
 "株式会社日本育児",
 "従業員34名・輸入・卸売専門",
 "全国（本社：大阪）",
 "〒541-0059 大阪市中央区博労町3-6-1 御堂筋エスジービル5F",
 "06-6251-7420",
 "https://www.nihonikuji.co.jp/contact/",
 "https://www.nihonikuji.co.jp/",
 "nihonikuji.co.jp/profile ／ prtimes.jp（ZOZO出店PR）",
 "Instagram: @nihonikuji_official",
 "代表取締役: 石迫壮馬 ／ 東京営業所: 千代田区岩本町2-4-1",
 "赤ちゃん本舗・トイザらス等への流通実績あり。東京営業所経由でアプローチ可"],

["F. 卸売・ディストリビューター","35",
 "NETSEA（ネッシー）",
 "国内最大級卸売プラットフォーム（ベビー28,000点超）",
 "全国（EC卸）",
 "東京都","","",
 "https://www.netsea.jp/category/105",
 "netsea.jp ／ WebSearch",
 "Instagram: @netsea_jp",
 "出品企業への卸売プラットフォーム",
 "出品登録でネットショップ・実店舗バイヤーに一括リーチ可"],

["F. 卸売・ディストリビューター","36",
 "スーパーデリバリー（株式会社ラクーンコマース）",
 "日本最大級・海外バイヤー対応も可",
 "全国＋海外（EC卸）",
 "〒103-0006 東京都中央区日本橋富沢町10-5",
 "03-4455-0444",
 "",
 "https://www.superdelivery.com/",
 "superdelivery.com ／ WebSearch",
 "Instagram: @superdelivery_jp",
 "日本製品を海外バイヤーへ卸せるプラットフォーム",
 "海外への輸出卸にも対応。グロミミの海外展開に活用可"],

# ===== G. その他ベビー専門 =====
["G. その他ベビー専門","37",
 "赤ちゃんデパート河田（赤ちゃんタウン）",
 "実店舗＋楽天EC",
 "東京",
 "東京都","","",
 "https://www.rakuten.co.jp/babytown/",
 "rakuten.co.jp/babytown/ ／ WebSearch",
 "楽天市場: 赤ちゃんデパート河田",
 "マタニティ＆ベビー用品の総合専門店",
 "楽天出店先としての取引交渉。または直接問い合わせ"],

["G. その他ベビー専門","38",
 "PETIT BATEAU（プチバトー）日本法人",
 "国内数店舗＋EC",
 "全国（本社：東京）",
 "東京都","","",
 "https://www.petit-bateau.co.jp/",
 "petit-bateau.co.jp ／ WebSearch（セレクトショップ調査中に発見）",
 "Instagram: @petitbateau_jp",
 "フランス発の老舗ベビー・キッズブランド。日本法人あり",
 "高感度・高単価ベビーブランド。共同プロモーションのアプローチ可"],

["G. その他ベビー専門","39",
 "赤ちゃんの城（株式会社イワシタ）",
 "メーカー直販＋EC",
 "全国（本社：愛知）",
 "愛知県","","",
 "https://www.baby.co.jp/",
 "baby.co.jp/company/ ／ WebSearch（日本製ベビー用品メーカー調査）",
 "Instagram: @akachangarden",
 "新生児寝具・衣料専門。全商品日本製・国内生産",
 "日本製こだわり層へのリーチ。OEM・卸提案の余地あり"],

["G. その他ベビー専門","40",
 "KIDSMIO系列／キッズエンターテインメント",
 "ベビー用品輸入・卸・EC",
 "全国（EC）",
 "","","",
 "https://kids-ec.com/",
 "kids-ec.com ／ WebSearch（ベビー用品卸確認）",
 "Instagram: @kidsec_official",
 "ベビー用品・輸入玩具・出産お祝いの卸・仕入れ対応",
 "卸・仕入れ対応。問い合わせフォームから取引交渉"],

# ===== 追加10社（41〜50） =====

# ── B. 百貨店 追加 ──
["B. 百貨店（ベビー売場）","41",
 "株式会社そごう・西武",
 "全国17店舗（そごう10＋西武7）・セブン＆アイHD傘下",
 "全国（本社：東京/池袋）",
 "〒171-8569 東京都豊島区南池袋1-28-1",
 "03-3981-0111（池袋西武代表）",
 "https://www.sogo-seibu.co.jp/inquiry/",
 "https://www.sogo-seibu.co.jp/",
 "sogo-seibu.co.jp ／ Wikipedia ／ セブン＆アイHD IR",
 "Instagram: @sogoseibu ／ X: @sogo_seibu",
 "MD部門（キッズ・ベビー担当バイヤー）",
 "池袋西武・横浜そごうのMD担当へのアプローチ推奨。展示会または問い合わせフォーム"],

["B. 百貨店（ベビー売場）","42",
 "株式会社松屋（松屋銀座）",
 "2店舗（銀座・浅草）",
 "東京（銀座・浅草）",
 "〒104-8130 東京都中央区銀座3-6-1",
 "03-3567-1211（銀座本店代表）",
 "https://www.matsuya.com/contact/",
 "https://www.matsuya.com/",
 "matsuya.com ／ Wikipedia（松屋銀座）",
 "Instagram: @matsuya_ginza ／ X: @matsuya_ginza",
 "MD部門（ベビー・キッズ担当バイヤー）",
 "銀座の高感度百貨店。ラグジュアリー・セレクト系に強み。フォームまたは展示会でアプローチ"],

# ── C. セレクトショップ 追加 ──
["C. セレクトショップ","43",
 "gelato pique（株式会社マッシュスタイルラボ）",
 "国内200店舗以上・売上100億円超",
 "全国（本社：東京/渋谷）",
 "〒150-8510 東京都渋谷区渋谷2-22-3",
 "03-6434-1111（マッシュHD代表）",
 "https://gelato-pique.com/contact/",
 "https://gelato-pique.com/",
 "gelato-pique.com ／ mash-style.com ／ prtimes.jp",
 "Instagram: @gelato_pique（700K+フォロワー）",
 "gelato pique事業部MD（マッシュスタイルラボ）",
 "Baby・Kidsライン展開中。ギフト・コラボ提案が有効。問い合わせフォームからアプローチ"],

["C. セレクトショップ","44",
 "niko and...（株式会社アダストリア）",
 "東証プライム上場・グループ売上2,000億円超・国内外1,400店以上",
 "全国（本社：東京/渋谷）",
 "〒150-0021 東京都渋谷区恵比寿西1-34-1",
 "0120-601-612（お客様窓口）",
 "https://www.adastria.co.jp/contact/",
 "https://www.nikoand.jp/",
 "nikoand.jp ／ adastria.co.jp ／ 東証IR情報",
 "Instagram: @nikoand_official ／ X: @nikoand_pr",
 "niko and...担当MD（アダストリア商品本部）",
 "キッズ・ベビーライン展開。ライフスタイル提案型。コラボ・バイイング共にアプローチ可"],

# ── D. EC・通販 追加 ──
["D. EC・通販","45",
 "株式会社ZOZO（ZOZOTOWN）",
 "東証プライム上場・年商2,000億円超・会員1,000万人以上",
 "全国（本社：千葉/千葉市）",
 "〒261-0023 千葉県千葉市美浜区中瀬1-7-1",
 "043-301-3000（代表）",
 "https://corp.zozo.com/contact/",
 "https://zozo.jp/shop/baby-kids/",
 "corp.zozo.com ／ 東証IR情報 ／ zozo.jp（ベビー・キッズカテゴリ）",
 "Instagram: @zozo_official ／ X: @ZOZOTOWN_PR",
 "ZOZO出店MD担当（キッズ・ベビー部門）",
 "国内最大EC。多数のベビーブランドが出店中。出店申請フォームからアプローチ"],

["D. EC・通販","46",
 "Qoo10 Japan（ギオシスジャパン合同会社）",
 "月間1,200万人利用・韓国系EC・日本市場急成長",
 "全国（本社：東京/品川）",
 "〒141-0032 東京都品川区大崎1-11-2",
 "",
 "https://www.qoo10.jp/seller/",
 "https://www.qoo10.jp/",
 "qoo10.jp ／ WebSearch（韓国ブランド出品多数確認）",
 "Instagram: @qoo10japan ／ X: @Qoo10_Japan",
 "出店担当MD: 出店申請フォームより",
 "韓国系ブランド（grosmimi等）との親和性が高い。セラー登録後すぐ出品開始可"],

["D. EC・通販","47",
 "株式会社フェリシモ",
 "東証プライム上場・通販大手・会員100万人超",
 "全国（本社：兵庫/神戸）",
 "〒650-0041 兵庫県神戸市中央区新港町7番1号",
 "0120-055-820（お客様窓口）",
 "https://www.felissimo.co.jp/company/contact/",
 "https://www.felissimo.co.jp/",
 "felissimo.co.jp/company/ ／ Wikipedia",
 "Instagram: @felissimo_official ／ X: @FELISSIMO",
 "商品担当バイヤー（ベビー・マタニティ部門）",
 "カタログ・EC掲載交渉が有効。ブランド認知向上に繋がる。問い合わせフォームから"],

# ── G. その他ベビー専門 追加 ──
["G. その他ベビー専門","48",
 "株式会社コンビ",
 "東証スタンダード上場・売上約137億円・従業員約370名",
 "全国（本社：東京/文京区）",
 "〒112-8560 東京都文京区大塚3-14-5",
 "03-5978-2300（代表）",
 "https://www.combi.co.jp/inquiry/",
 "https://www.combi.co.jp/",
 "combi.co.jp/company/ ／ 東証IR情報 ／ Wikipedia",
 "Instagram: @combi_official_jp ／ X: @COMBI_info",
 "代表取締役社長: 坂本一喜 ／ 営業部（卸・取引相談）",
 "ベビーカー・チャイルドシート大手。卸・共同展開の提案余地あり。問い合わせフォームから"],

["G. その他ベビー専門","49",
 "株式会社ニトリホールディングス",
 "全国930店舗以上・東証プライム上場・売上9,000億円超",
 "全国（本社：北海道/札幌）",
 "〒001-0907 北海道札幌市北区新琴似七条1-2-39",
 "011-330-9000（代表）",
 "https://www.nitori-net.jp/customer/inquiry/",
 "https://www.nitori-net.jp/",
 "nitorihd.co.jp ／ 東証IR情報 ／ Wikipedia",
 "Instagram: @nitori_official ／ X: @nitoriofficial",
 "商品部（ベビー・キッズ担当MD）",
 "ベビー寝具・インテリア用品コーナーあり。取引申請フォームからアプローチ"],

["G. その他ベビー専門","50",
 "株式会社スタジオアリス",
 "全国550店舗以上・東証プライム上場",
 "全国（本社：大阪/大阪市）",
 "〒530-0003 大阪府大阪市北区堂島1-5-17",
 "06-6344-8181（代表）",
 "https://www.studio-alice.co.jp/contact/",
 "https://www.studio-alice.co.jp/",
 "studio-alice.co.jp ／ 東証IR情報 ／ Wikipedia",
 "Instagram: @studioalice_official ／ X: @STUDIO_ALICE",
 "商品開発部・MD部門（グッズ関連担当）",
 "ベビー写真＋ギフトグッズ販売あり。撮影衣装・小物のコラボ提案が有効。フォームから"],
]

# A→G順に並べ替え・通し番号振り直し
CAT_ORDER = ["A.", "B.", "C.", "D.", "E.", "F.", "G."]
rows.sort(key=lambda r: next((i for i, c in enumerate(CAT_ORDER) if r[0].startswith(c)), 99))
for i, row in enumerate(rows):
    row[1] = str(i + 1)

import re

def extract_url(text):
    m = re.search(r'https?://[^\s　（）()]+', text)
    return m.group(0).rstrip('）)') if m else None

LINK_COLS = {H.index("公式URL"), H.index("卸・問い合わせ先")}

def build_row(row):
    r = list(row)
    for ci in LINK_COLS:
        if ci < len(r) and r[ci]:
            url = extract_url(r[ci])
            if url:
                r[ci] = f'=HYPERLINK("{url}","{r[ci].replace(chr(34), chr(39))}")'
    return r

all_data = [H] + [build_row(r) for r in rows]
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range=f"{SHEET_NAME}!A1",
    valueInputOption="USER_ENTERED", body={"values": all_data},
).execute()

print("Data written.")

# ── 書式設定 ─────────────────────────────────────────────────────────────────
CAT_COLOR = {
    "A. 大手ベビー専門チェーン":      {"red":0.98,"green":0.80,"blue":0.76},
    "B. 百貨店（ベビー売場）":        {"red":0.98,"green":0.90,"blue":0.70},
    "C. セレクトショップ":            {"red":0.79,"green":0.91,"blue":0.97},
    "D. EC・通販":                    {"red":0.85,"green":0.92,"blue":0.83},
    "E. 小規模セレクトショップ":      {"red":0.93,"green":0.87,"blue":0.98},
    "F. 卸売・ディストリビューター":  {"red":0.80,"green":0.95,"blue":0.95},
    "G. その他ベビー専門":            {"red":0.94,"green":0.94,"blue":0.94},
}
PRI_COLOR = {
    "最優先": {"red":0.95,"green":0.27,"blue":0.27},
    "次点":   {"red":0.98,"green":0.60,"blue":0.00},
    "中長期": {"red":0.30,"green":0.69,"blue":0.31},
}

reqs = []

# ヘッダー
reqs.append({"repeatCell":{
    "range":{"sheetId":sheet_id,"startRowIndex":0,"endRowIndex":1},
    "cell":{"userEnteredFormat":{
        "backgroundColor":{"red":0.15,"green":0.15,"blue":0.15},
        "textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":True,"fontSize":10},
        "horizontalAlignment":"CENTER","verticalAlignment":"MIDDLE","wrapStrategy":"WRAP",
    }},
    "fields":"userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
}})

for i, row in enumerate(rows):
    ri = i + 1
    cat, pri = row[0], row[1]
    # カテゴリ列
    reqs.append({"repeatCell":{
        "range":{"sheetId":sheet_id,"startRowIndex":ri,"endRowIndex":ri+1,"startColumnIndex":0,"endColumnIndex":1},
        "cell":{"userEnteredFormat":{
            "backgroundColor":CAT_COLOR.get(cat,{"red":1,"green":1,"blue":1}),
            "textFormat":{"bold":True,"fontSize":9},
            "wrapStrategy":"WRAP","verticalAlignment":"MIDDLE",
        }},
        "fields":"userEnteredFormat(backgroundColor,textFormat,wrapStrategy,verticalAlignment)",
    }})
    # 優先度列
    reqs.append({"repeatCell":{
        "range":{"sheetId":sheet_id,"startRowIndex":ri,"endRowIndex":ri+1,"startColumnIndex":1,"endColumnIndex":2},
        "cell":{"userEnteredFormat":{
            "backgroundColor":PRI_COLOR.get(pri,{"red":0.8,"green":0.8,"blue":0.8}),
            "textFormat":{"bold":True,"foregroundColor":{"red":1,"green":1,"blue":1},"fontSize":9},
            "horizontalAlignment":"CENTER","verticalAlignment":"MIDDLE",
        }},
        "fields":"userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)",
    }})
    # データ列
    bg = {"red":1,"green":1,"blue":1} if i%2==0 else {"red":0.97,"green":0.97,"blue":0.97}
    reqs.append({"repeatCell":{
        "range":{"sheetId":sheet_id,"startRowIndex":ri,"endRowIndex":ri+1,"startColumnIndex":2,"endColumnIndex":len(H)},
        "cell":{"userEnteredFormat":{
            "backgroundColor":bg,
            "textFormat":{"fontSize":9},
            "wrapStrategy":"WRAP","verticalAlignment":"MIDDLE",
        }},
        "fields":"userEnteredFormat(backgroundColor,textFormat,wrapStrategy,verticalAlignment)",
    }})

# 列幅（14列）
col_w = [165,50,220,200,140,200,140,220,220,200,220,200,220,240]
for ci,w in enumerate(col_w):
    reqs.append({"updateDimensionProperties":{
        "range":{"sheetId":sheet_id,"dimension":"COLUMNS","startIndex":ci,"endIndex":ci+1},
        "properties":{"pixelSize":w},"fields":"pixelSize",
    }})

# 行高さ
reqs.append({"updateDimensionProperties":{
    "range":{"sheetId":sheet_id,"dimension":"ROWS","startIndex":0,"endIndex":1},
    "properties":{"pixelSize":36},"fields":"pixelSize",
}})
reqs.append({"updateDimensionProperties":{
    "range":{"sheetId":sheet_id,"dimension":"ROWS","startIndex":1,"endIndex":len(rows)+1},
    "properties":{"pixelSize":70},"fields":"pixelSize",
}})

# 罫線
reqs.append({"updateBorders":{
    "range":{"sheetId":sheet_id,"startRowIndex":0,"endRowIndex":len(rows)+1,
             "startColumnIndex":0,"endColumnIndex":len(H)},
    "innerHorizontal":{"style":"SOLID","color":{"red":0.8,"green":0.8,"blue":0.8}},
    "innerVertical":  {"style":"SOLID","color":{"red":0.8,"green":0.8,"blue":0.8}},
    "top":   {"style":"SOLID_MEDIUM","color":{"red":0.2,"green":0.2,"blue":0.2}},
    "bottom":{"style":"SOLID_MEDIUM","color":{"red":0.2,"green":0.2,"blue":0.2}},
    "left":  {"style":"SOLID_MEDIUM","color":{"red":0.2,"green":0.2,"blue":0.2}},
    "right": {"style":"SOLID_MEDIUM","color":{"red":0.2,"green":0.2,"blue":0.2}},
}})

# 先頭行固定
reqs.append({"updateSheetProperties":{
    "properties":{"sheetId":sheet_id,"gridProperties":{"frozenRowCount":1}},
    "fields":"gridProperties.frozenRowCount",
}})

svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests":reqs}).execute()
print("Formatting applied.")
print(f"\n完成: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
