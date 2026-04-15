"""
Grosmimi 子どもが飲んでる動画 コンテンツガイドライン Word生成
"""

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def add_cell_text(cell, text, bold=False, size=10, color=None, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ''
    para = cell.paragraphs[0]
    para.alignment = align
    run = para.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_section_header(doc, text, bg_hex, text_color=(255, 255, 255), size=12):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_bg(cell, bg_hex)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(*text_color)
    doc.add_paragraph()


def add_idea_table(doc, number, title, category_color, hook, visual, caption, point):
    """1アイデア分のテーブルを追加"""
    # タイトル行
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    set_cell_bg(cell, category_color)
    p = cell.paragraphs[0]
    run = p.add_run(f'No.{number}　{title}')
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(255, 255, 255)

    # 内容テーブル
    content_table = doc.add_table(rows=4, cols=2)
    content_table.style = 'Table Grid'

    rows_data = [
        ('フック（冒頭）', hook),
        ('撮影シーン', visual),
        ('キャプション例', caption),
        ('バズりポイント', point),
    ]

    label_widths = [3.0, 14.0]
    label_bgs = ['F5F5F5', 'FFFFFF']

    for i, (label, value) in enumerate(rows_data):
        c0 = content_table.cell(i, 0)
        c1 = content_table.cell(i, 1)
        set_cell_bg(c0, 'EFEFEF')
        set_cell_bg(c1, label_bgs[i % 2])
        add_cell_text(c0, label, bold=True, size=9)
        add_cell_text(c1, value, size=9)
        c0.width = Cm(label_widths[0])
        c1.width = Cm(label_widths[1])

    doc.add_paragraph()


def add_requirements_section(doc):
    """必須要件セクションを追加"""
    title_table = doc.add_table(rows=1, cols=1)
    title_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = title_table.cell(0, 0)
    set_cell_bg(cell, '2C2C2C')
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('GROSMIMI JAPAN　インフルエンサー向けコンテンツガイドライン')
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(255, 255, 255)
    doc.add_paragraph()

    intro = doc.add_paragraph()
    ir = intro.add_run('平素よりお世話になっております。\n以下は、今回の動画制作・投稿に関する必須要件となります。ご確認の上、ご対応をお願いいたします。')
    ir.font.size = Pt(10)
    doc.add_paragraph()

    add_section_header(doc, '必須要件', 'C0392B', (255, 255, 255), 11)

    requirements = [
        ('オリジナル動画\nファイルの提供',
         '・弊社での二次利用を想定して、オリジナル動画ファイルをご提供ください。\n'
         '・使用する音楽は著作権フリーのものをご使用ください。\n'
         '・動画内に字幕（テロップ）は含めずにご提出ください。'),
        ('ホワイトリスト\nコードの付与',
         '・投稿用にホワイトリストコードへのアクセス許可をお願いいたします。'),
        ('投稿用動画\nコンテンツ',
         '・インフルエンサー様が実際にSNSにアップロードする動画です。\n'
         '・動画には必ずナレーション（音声）と字幕を含めてください。\n\n'
         '【Instagramでの投稿について】\n'
         '投稿時には共同投稿（コラボ投稿）として\nGROSMIMI（grosmimi_japan）アカウントを設定してください。'),
        ('納期',
         '・商品到着後、3週間以内にコンテンツをアップロードしてください。'),
        ('確認・承認',
         '・投稿前に弊社チームにて内容を確認・承認させていただきます。\n'
         '・承認完了後にアップロードをお願いいたします。'),
    ]

    req_table = doc.add_table(rows=len(requirements), cols=2)
    req_table.style = 'Table Grid'
    for i, (label, value) in enumerate(requirements):
        c0 = req_table.cell(i, 0)
        c1 = req_table.cell(i, 1)
        set_cell_bg(c0, 'FDEDEC')
        add_cell_text(c0, label, bold=True, size=9)
        add_cell_text(c1, value, size=9)
        c0.width = Cm(3.5)
        c1.width = Cm(13.5)
    doc.add_paragraph()
    doc.add_page_break()


def main():
    doc = Document()

    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)

    doc.styles['Normal'].font.name = 'Yu Gothic'
    doc.styles['Normal'].font.size = Pt(10)

    add_requirements_section(doc)

    # ---- メインタイトル ----
    title_table = doc.add_table(rows=1, cols=1)
    title_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = title_table.cell(0, 0)
    set_cell_bg(cell, '2C2C2C')
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('子どもが飲んでる動画　コンテンツガイドライン')
    run.bold = True
    run.font.size = Pt(15)
    run.font.color.rgb = RGBColor(255, 255, 255)
    doc.add_paragraph()

    # ---- 前置き ----
    intro = doc.add_paragraph()
    ir = intro.add_run(
        'このガイドラインは「商品紹介」ではなく「子どもの自然な姿」を主役にしたコンテンツ用です。\n'
        'Grosmimiのストローマグは脇役として映り込む程度でOK。\n'
        '子どもの表情・反応・行動がコンテンツのすべてです。'
    )
    ir.font.size = Pt(10)
    ir.font.color.rgb = RGBColor(80, 80, 80)
    doc.add_paragraph()

    cat_intro = doc.add_paragraph()
    ci = cat_intro.add_run(
        '下記のカテゴリを参考に、動画の制作をお願いいたします。\n'
        'カテゴリごとにシーン構成・撮影ポイント・キャプション例を記載していますので、'
        'ご自身のスタイルに合ったものをお選びください。\n'
        '複数のカテゴリを組み合わせていただいても構いません。'
    )
    ci.bold = True
    ci.font.size = Pt(10)
    ci.font.color.rgb = RGBColor(30, 30, 30)
    doc.add_paragraph()

    # ---- 共通撮影ルール ----
    add_section_header(doc, '共通撮影ルール', '4A90D9', (255, 255, 255), 11)

    rules_table = doc.add_table(rows=6, cols=2)
    rules_table.style = 'Table Grid'
    rules = [
        ('縦型撮影', '9:16（リール対応）で撮影'),
        ('明るさ', '自然光推奨。窓際・昼間がベスト'),
        ('尺', '15〜30秒が理想。山場のシーンは長めに録っておく'),
        ('音', '飲む音・笑い声・環境音はそのまま残す（カットしない）'),
        ('字幕', '全ナレーションに字幕を入れる'),
        ('マグの映り方', 'さりげなく映り込む程度でOK。商品アップは不要'),
    ]
    for i, (label, val) in enumerate(rules):
        c0 = rules_table.cell(i, 0)
        c1 = rules_table.cell(i, 1)
        set_cell_bg(c0, 'EFEFEF')
        add_cell_text(c0, label, bold=True, size=9)
        add_cell_text(c1, val, size=9)
        c0.width = Cm(3.5)
        c1.width = Cm(13.5)
    doc.add_paragraph()

    # ==============================
    # カテゴリ1：感動・初めて系
    # ==============================
    add_section_header(doc, 'カテゴリ1　感動・初めて系', 'E67E22', (255, 255, 255), 11)

    ideas_cat1 = [
        (1, '初めてストローで飲めた瞬間',
         '「2ヶ月挑戦してたんやけど…」',
         '・ストローを口に近づける場面から録画開始\n・成功した瞬間の顔アップ（口元 + 目が両方映る角度）\n・親のリアクションも入れてOK（むしろ欲しい）',
         '「飲めた！！！！！」のテキストだけでいい。言葉はいらない',
         '「初めての瞬間」は必ず保存・シェアされる。コメント爆増パターン'),

        (2, '初めて自分でマグを持って飲めた瞬間',
         '「え、もう自分で持てるの…？」',
         '・両手でよろよろ持ち上げる瞬間から撮る\n・成功したときの得意げな顔を逃さない\n・スローモーションにするとさらに映える',
         '「気づいたらひとりで飲んでた。成長が速すぎて追いつかない」',
         '「うちも同じだった！」の共感コメントが集まる'),

        (3, '初めて「もっとちょうだい」サインをした瞬間',
         '「え、今おかわりって言った？」',
         '・空になったマグを差し出してくる場面\n・逆さにして「ない」と気づく一連の流れ\n・困り顔 or 催促する表情のアップ',
         '「空っぽになったのを自分で気づいてた。もう赤ちゃんじゃないな」',
         'かわいいと賢さが同時に見えるのでコメントが止まらない'),
    ]

    for num, title, hook, visual, caption, point in ideas_cat1:
        add_idea_table(doc, num, title, 'E67E22', hook, visual, caption, point)

    doc.add_page_break()

    # ==============================
    # カテゴリ2：コミカル・あるある系
    # ==============================
    add_section_header(doc, 'カテゴリ2　コミカル・あるある系', '27AE60', (255, 255, 255), 11)

    ideas_cat3 = [
        (4, '飲みながら踊ってる',
         '「マグくわえたまま踊り始めた」',
         '・音楽や好きな動画が流れてるときに飲んでいる場面\n・体を揺らしながらストローをくわえてる姿を正面から\n・リズムに合ってると最高',
         '「マグ離さないのに踊るの器用すぎる笑」',
         'BGMをつけて投稿するとループ再生されやすい。音楽バズり狙える'),

        (5, '飲み終わったか逆さにして確認するやつ',
         '「空になったのを絶対認めようとしない笑」',
         '・マグが空になる → ちゅーちゅーしても出ない\n・逆さにして確認する動作\n・「ない」と気づいて困り顔になる一連の流れ',
         '「空って認めるまでが長い笑」',
         '「うちもこれやる！！」の共感コメントが止まらないあるある動画'),

        (6, 'ストロー噛みながらカメラと目が合う',
         '「飲んでるとき目が合ったら動きが止まった」',
         '・飲んでいる最中にカメラを向ける\n・目が合った瞬間にぴたっと止まる場面\n・じーっとこちらを見る顔のアップ\n・数秒後にまた飲み始めるまで撮る',
         '「なんで止まるの笑　監視されてるみたいな目してた」',
         '「目が合う瞬間」系は無条件でかわいい。保存率が高い'),

        (7, 'マグをくわえたままどこかへ歩いていく',
         '「飲むのやめずにどこ行くの笑」',
         '・ストローをくわえたまま別の方向へ歩き出す\n・後ろ姿を追いかけながら撮る\n・ちょこちょこ歩く姿が映えるとベスト',
         '「飲みながら散歩に行きだした笑」',
         '後ろ姿 + ちょこちょこ歩き = かわいい。コメントが「天使」で埋まる'),

        (8, '眉間にしわを寄せて一生懸命飲んでる',
         '「なんでそんな真剣な顔してるの笑」',
         '・ストロー飲みに集中しているときの顔アップ\n・眉間のしわと真剣な目をアップで撮る\n・飲み終わってぱっと顔が緩む瞬間まで撮ると完璧',
         '「何をそんなに考えながら飲んでるの笑」',
         '真剣 × かわいいのギャップが刺さる。「うちも同じ顔する！」コメント多数'),

        (9, '飲み終わった後に「ぷはー」顔をする',
         '「飲み終わったときの顔が毎回おもしろい」',
         '・飲んでいる場面からそのまま撮り続ける\n・口を離した瞬間の表情をアップで\n・スローモーションにすると表情の変化が映える',
         '「ぷはーってした顔が大人みたいで笑えた」',
         'スロー再生との相性が抜群。TikTokで伸びやすいフォーマット'),
    ]

    for num, title, hook, visual, caption, point in ideas_cat3:
        add_idea_table(doc, num, title, '27AE60', hook, visual, caption, point)

    doc.add_page_break()

    # ==============================
    # カテゴリ3：日常・癒し系
    # ==============================
    add_section_header(doc, 'カテゴリ3　日常・癒し系', 'C0392B', (255, 255, 255), 11)

    ideas_cat5 = [
        (10, '朝一番に飲んでるシーン',
         '「うちの子の一日はこれで始まる」',
         '・起きてすぐ・寝ぼけ顔でマグを抱えてる朝の場面\n・ぼーっとした顔で飲んでる姿を自然光で\n・こちらが声をかけても反応が薄いとなお良い',
         '「朝一は無言でこれを飲む。大人と同じ笑」',
         '「うちも！」の共感コメントが集まる朝ルーティン系'),

        (11, 'お風呂上がりに一気飲み',
         '「お風呂上がりだけはガチで飲む」',
         '・お風呂上がりでまだ少し濡れてる状態\n・ごくごく飲んでいる音が入るように静かな環境で\n・飲み終わった満足げな顔まで撮る',
         '「お風呂上がりの一杯だけは絶対本気で飲む笑」',
         '「のどが渇いてる感」のリアルさが刺さる。大人も共感できる'),

        (12, '離乳食中にちょっと一口飲むシーン',
         '「食事中のこの間が好きすぎる」',
         '・ご飯を食べながらふとマグに手を伸ばす場面\n・一口飲んでまたご飯に戻る自然な流れ\n・食卓全体の雰囲気ごと撮る（俯瞰もよい）',
         '「この何気ない食卓の風景、ずっと覚えてたい」',
         '日常の美しさを切り取った系。保存率が高い'),

        (13, '寝る前の最後の一杯',
         '「パジャマ姿でうとうとしながら飲んでる姿がたまらない」',
         '・パジャマ姿・少し眠そうな状態でマグを持ってる場面\n・目がとろんとしながら飲んでる顔のアップ\n・飲み終わってそのまま眠くなる流れまで撮れると最高',
         '「飲みながら寝そうになってた。今日もお疲れ様」',
         '「寝かしつけ前の儀式」として共感を呼ぶ。夜に見る人に刺さる'),
    ]

    for num, title, hook, visual, caption, point in ideas_cat5:
        add_idea_table(doc, num, title, 'C0392B', hook, visual, caption, point)

    doc.add_page_break()

    # ==============================
    # カテゴリ4：飲みっぷり（먹方）系
    # ==============================
    add_section_header(doc, 'カテゴリ4　飲みっぷり（먹方）系', 'D35400', (255, 255, 255), 11)

    cat4_note = doc.add_paragraph()
    nr = cat4_note.add_run('飲むことに全集中してる赤ちゃんの顔がコンテンツの核。マグは映ってるだけでOK。テキストだけで成立する構成にする。')
    nr.italic = True
    nr.font.size = Pt(9)
    nr.font.color.rgb = RGBColor(100, 100, 100)
    doc.add_paragraph()

    ideas_cat4 = [
        (14, '飲みっぷりが良すぎる',
         '「この集中力どこから来てるの」',
         '・ストローマグをくわえて一心不乱に飲んでる顔の超アップ\n'
         '・眉間・目・口元が全部映る角度（正面〜やや上から）\n'
         '・飲んでる間ずっと顔を撮り続ける\n'
         '・途中で目が合う / 一瞬止まってまた飲み始める / 飲み終わって「ぷはー」の流れまで撮る\n'
         '・飲む音（チュッチュッ）はそのまま残す\n'
         '・マグのアップ不要。映ってればOK',
         '「飲みっぷりが良すぎる」\n「毎回この顔する笑」\n「この集中力どこから来てるの」',
         'テキストだけで成立。ナレーション不要。無音でも見られる構成が強い'),

        (15, '飲んでる途中で目が合った',
         '「飲んでるとき目が合ったら動きが止まった笑」',
         '・飲んでいる最中にカメラをそっと近づける\n'
         '・目が合った瞬間にぴたっと止まる場面\n'
         '・数秒じーっとこちらを見る顔のアップ\n'
         '・また飲み始めるまでカットしない',
         '「目が合ったら止まった笑　なんで」\n「監視されてるみたいな目してた」',
         '「目が合う瞬間」は無条件でかわいい。保存率・コメント率ともに高い'),
    ]

    for num, title, hook, visual, caption, point in ideas_cat4:
        add_idea_table(doc, num, title, 'D35400', hook, visual, caption, point)

    doc.add_page_break()

    # ==============================
    # カテゴリ5：月齢記念演出系
    # ==============================
    add_section_header(doc, 'カテゴリ5　月齢記念演出系', '8E44AD', (255, 255, 255), 11)

    cat5_note = doc.add_paragraph()
    nr2 = cat5_note.add_run('Grosmimiのストローマグを「このマグと一緒に育ってきた」という時間軸で見せる。マグが成長記録の象徴になる。')
    nr2.italic = True
    nr2.font.size = Pt(9)
    nr2.font.color.rgb = RGBColor(100, 100, 100)
    doc.add_paragraph()

    ideas_cat5b = [
        (16, 'LEDキャンドル演出',
         '「〇ヶ月おめでとう」',
         '・Grosmimiのマグをテーブルに置くまたは赤ちゃんに持たせる\n'
         '・マグの横にLEDキャンドルを数本並べて灯す\n'
         '・「〇ヶ月おめでとう」テキストを重ねる\n'
         '・部屋を少し暗くするとキャンドルの光が映えてきれい\n'
         '・ゆらゆら揺れる光を見てる赤ちゃんの表情を撮る\n'
         '※火を使わないLEDなので安心して使用できる',
         '「〇ヶ月、おめでとう。このマグと一緒に大きくなったね」',
         '温かみのある光で雰囲気が出る。「うちもやりたい」のコメントが来る'),

        (17, 'バルーン × ライト演出',
         '「〇ヶ月おめでとう」',
         '・「〇」の数字バルーンを用意してマグの横に置く\n'
         '・バルーンの中にLEDライトを入れると内側から光ってキラキラになる\n'
         '・または背景にフェアリーライトを広げてキラキラの中でマグを持って飲んでる場面を撮る\n'
         '・赤ちゃんがバルーンやライトに興味を持って触ろうとする場面も映えるポイント',
         '「〇ヶ月、このバルーンより大きくなった笑」\n「キラキラの中で飲んでるの最高すぎた」',
         '数字バルーンは月齢がひと目でわかり、毎月投稿できるフォーマットになる'),

        (18, '月齢ボード × マグ',
         '「毎月この子とこのマグで写真撮ってる」',
         '・月齢ボードの横にGrosmimiのマグを並べる\n'
         '・子どもがマグを持ちながら月齢ボードの前に座ってる動画\n'
         '・毎月同じ構図・同じ場所で撮ると成長比較動画が作れる',
         '「毎月この子と、このマグで撮ってる。気づいたらもう〇ヶ月」',
         '毎月投稿できるフォーマット。継続することでフォロワーが増えやすい'),

        (19, '「このマグと〇ヶ月」振り返り',
         '「ストローマグデビューから〇ヶ月経った」',
         '・使い始めた頃の飲んでる動画 + 今の動画を並べる\n'
         '・最初は両手でよろよろ → 今は片手でさらっと、の対比\n'
         '・マグの大きさと子どもの成長サイズの変化が一目でわかる構図',
         '「ストローマグデビューしてから〇ヶ月。最初は全然飲めなかったのに」',
         '成長の変化が視覚的に伝わる。「泣いた」「うちも同じ」コメントが来る'),
    ]

    for num, title, hook, visual, caption, point in ideas_cat5b:
        add_idea_table(doc, num, title, '8E44AD', hook, visual, caption, point)

    doc.add_paragraph()

    # ---- NG事項 ----
    add_section_header(doc, 'NG事項（必ずご確認ください）', 'C0392B', (255, 255, 255), 11)

    ng_items = [
        ('冒頭の商品アップ',
         '動画の冒頭3秒以内に商品アップ・開封シーンから入らないでください。\n'
         'まず子どもの自然な表情・日常シーンから始めてください。'),
        ('宣伝・PR感',
         '「ブランドからいただきました」「提供品です」という表現や雰囲気を出さないでください。\n'
         '自分で選んだアイテムとして自然に紹介してください。'),
        ('ウォーターマーク',
         'テキストスタンプ・ウォーターマーク・他社ロゴは動画内に入れないでください。'),
        ('鏡写し・反転映像',
         '商品ラベル・ブランド名（Grosmimi）が反転して映る鏡写し映像はNGです。\n'
         '投稿前に文字が正しく読めるか必ず確認してください。'),
        ('著作権のある音楽',
         '著作権フリーの音楽のみ使用してください。\n'
         '人気楽曲・テレビ曲・アーティスト楽曲はNGです（二次利用時に問題になります）。'),
        ('未承認での投稿',
         '動画の投稿前に必ず弊社チームの確認・承認を受けてください。\n'
         '承認前のアップロードはお控えください。'),
    ]

    ng_table = doc.add_table(rows=len(ng_items), cols=2)
    ng_table.style = 'Table Grid'
    for i, (label, value) in enumerate(ng_items):
        c0 = ng_table.cell(i, 0)
        c1 = ng_table.cell(i, 1)
        set_cell_bg(c0, 'FDEDEC')
        set_cell_bg(c1, 'FFF5F5' if i % 2 == 0 else 'FFFFFF')
        add_cell_text(c0, label, bold=True, size=9, color=(180, 0, 0))
        add_cell_text(c1, value, size=9)
        c0.width = Cm(3.5)
        c1.width = Cm(13.5)

    doc.add_paragraph()

    # ---- タグ ----
    add_section_header(doc, 'タグ', '2C2C2C', (255, 255, 255), 10)
    tag_table = doc.add_table(rows=2, cols=2)
    tag_table.style = 'Table Grid'
    set_cell_bg(tag_table.cell(0, 0), '2C2C2C')
    set_cell_bg(tag_table.cell(0, 1), '2C2C2C')
    add_cell_text(tag_table.cell(0, 0), 'Instagram', bold=True, size=9, color=(255, 255, 255))
    add_cell_text(tag_table.cell(0, 1), '@grosmimi_japan', size=9, color=(255, 255, 255))
    add_cell_text(tag_table.cell(1, 0), 'ハッシュタグ', bold=True, size=9)
    add_cell_text(tag_table.cell(1, 1), '#グロミミ #Grosmimi #ストローマグ #スマートマグ #赤ちゃんのいる生活 #育児記録', size=9)
    for row in tag_table.rows:
        row.cells[0].width = Cm(3.0)
        row.cells[1].width = Cm(14.0)

    output_path = ".tmp/Grosmimi_BabyDrinking_Guideline_JP.docx"
    doc.save(output_path)
    print(f"Done: {output_path}")


if __name__ == "__main__":
    main()
