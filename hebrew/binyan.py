#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 態の型 (binyan) の表: 同じ語根から、態ごとにどんな形ができるか
#
#   python3 hebrew.py --binyan כתב      (ラテン文字でも: --binyan ktb)
#
#   qal (paʿal パアル): 基本の態。能動の単純な動作
#     完了 3男単      kātav       כָּתַב      ×10
#     未完了 3男単    yiḵtōv      יִכְתֹּב     ×6
#     …
#   hiphil (hifʿil ヒフイル): 使役「〜させる」
#     完了 3男単    * hiḵtîv      הִכְתִּיב   (聖書に無い。規則どおりに作った形)
#
# 形は Open Scriptures Hebrew Bible に現れたもの (多いもの) を使い、無いものは強い語根の型から作って * を付ける。
# 喉音 (א ה ח ע ר) や弱い字 (語頭の נ・י・ו、2字目の ו・י、語末の ה、2字目と3字目が同じ) を含む語根では、
# 作った形が実際の形と違うことがある
#
import unicodedata

from . import dictionary, explain, script

POINT = {'sheva': 'ְ', 'hiriq': 'ִ', 'tsere': 'ֵ', 'segol': 'ֶ', 'patah': 'ַ',
         'qamats': 'ָ', 'holam': 'ֹ', 'qubuts': 'ֻ', 'qamats_qatan': 'ׇ', '': ''}
DAGESH = 'ּ'
SHIN_DOT = 'ׁ'
BGDKPT = set('בגדכפת')
GUTTURALS = set('אהחער')
FINAL = {'כ': 'ך', 'מ': 'ם', 'נ': 'ן', 'פ': 'ף', 'צ': 'ץ'}

# 型: 部分の列。(字, 母音, ダゲシュ)。字が 1 2 3 なら語根の字。ダゲシュは 'F' (重ねる) / 'L' (begadkefat なら付ける) / ''
# 母音の 'yod' は ִי (hiriq + י)
TEMPLATES = {
    'qal': {'qatal': [(1, 'qamats', 'L'), (2, 'patah', ''), (3, '', '')],
            'yiqtol': [('י', 'hiriq', ''), (1, 'sheva', ''), (2, 'holam', 'L'), (3, '', '')],
            'imperative': [(1, 'sheva', 'L'), (2, 'holam', ''), (3, '', '')],
            'participle': [(1, 'holam', 'L'), (2, 'tsere', ''), (3, '', '')],
            'infinitive': [(1, 'sheva', 'L'), (2, 'holam', ''), (3, '', '')]},
    'niphal': {'qatal': [('נ', 'hiriq', ''), (1, 'sheva', ''), (2, 'patah', 'L'), (3, '', '')],
               'yiqtol': [('י', 'hiriq', ''), (1, 'qamats', 'F'), (2, 'tsere', ''), (3, '', '')],
               'imperative': [('ה', 'hiriq', ''), (1, 'qamats', 'F'), (2, 'tsere', ''), (3, '', '')],
               'participle': [('נ', 'hiriq', ''), (1, 'sheva', ''), (2, 'qamats', 'L'), (3, '', '')],
               'infinitive': [('ה', 'hiriq', ''), (1, 'qamats', 'F'), (2, 'tsere', ''), (3, '', '')]},
    'piel': {'qatal': [(1, 'hiriq', 'L'), (2, 'tsere', 'F'), (3, '', '')],
             'yiqtol': [('י', 'sheva', ''), (1, 'patah', ''), (2, 'tsere', 'F'), (3, '', '')],
             'imperative': [(1, 'patah', 'L'), (2, 'tsere', 'F'), (3, '', '')],
             'participle': [('מ', 'sheva', ''), (1, 'patah', ''), (2, 'tsere', 'F'), (3, '', '')],
             'infinitive': [(1, 'patah', 'L'), (2, 'tsere', 'F'), (3, '', '')]},
    'pual': {'qatal': [(1, 'qubuts', 'L'), (2, 'patah', 'F'), (3, '', '')],
             'yiqtol': [('י', 'sheva', ''), (1, 'qubuts', ''), (2, 'patah', 'F'), (3, '', '')],
             'participle': [('מ', 'sheva', ''), (1, 'qubuts', ''), (2, 'qamats', 'F'), (3, '', '')],
             'infinitive': [(1, 'qubuts', 'L'), (2, 'patah', 'F'), (3, '', '')]},
    'hiphil': {'qatal': [('ה', 'hiriq', ''), (1, 'sheva', ''), (2, 'yod', 'L'), (3, '', '')],
               'yiqtol': [('י', 'patah', ''), (1, 'sheva', ''), (2, 'yod', 'L'), (3, '', '')],
               'imperative': [('ה', 'patah', ''), (1, 'sheva', ''), (2, 'tsere', 'L'), (3, '', '')],
               'participle': [('מ', 'patah', ''), (1, 'sheva', ''), (2, 'yod', 'L'), (3, '', '')],
               'infinitive': [('ה', 'patah', ''), (1, 'sheva', ''), (2, 'yod', 'L'), (3, '', '')]},
    'hophal': {'qatal': [('ה', 'qamats_qatan', ''), (1, 'sheva', ''), (2, 'patah', 'L'), (3, '', '')],
               'yiqtol': [('י', 'qamats_qatan', ''), (1, 'sheva', ''), (2, 'patah', 'L'), (3, '', '')],
               'participle': [('מ', 'qamats_qatan', ''), (1, 'sheva', ''), (2, 'qamats', 'L'), (3, '', '')],
               'infinitive': [('ה', 'qamats_qatan', ''), (1, 'sheva', ''), (2, 'patah', 'L'), (3, '', '')]},
    'hithpael': {'qatal': [('ה', 'hiriq', ''), ('ת', 'sheva', ''), (1, 'patah', 'L'), (2, 'tsere', 'F'), (3, '', '')],
                 'yiqtol': [('י', 'hiriq', ''), ('ת', 'sheva', ''), (1, 'patah', 'L'), (2, 'tsere', 'F'),
                            (3, '', '')],
                 'imperative': [('ה', 'hiriq', ''), ('ת', 'sheva', ''), (1, 'patah', 'L'), (2, 'tsere', 'F'),
                                (3, '', '')],
                 'participle': [('מ', 'hiriq', ''), ('ת', 'sheva', ''), (1, 'patah', 'L'), (2, 'tsere', 'F'),
                                (3, '', '')],
                 'infinitive': [('ה', 'hiriq', ''), ('ת', 'sheva', ''), (1, 'patah', 'L'), (2, 'tsere', 'F'),
                                (3, '', '')]},
}
STEMS = ['qal', 'niphal', 'piel', 'pual', 'hiphil', 'hophal', 'hithpael']
STEM_CODES = {'qal': 'q', 'niphal': 'N', 'piel': 'p', 'pual': 'P', 'hiphil': 'h', 'hophal': 'H', 'hithpael': 't'}
# 2字目が ו・י の語根 (中空動詞) は piel・pual・hithpael の代わりに polel・polal・hithpolel (קוֹמֵם qômēm)、
# 重複語根 (2字目と3字目が同じ) は piel 系 (הִלֵּל) か poel・poal・hithpoel (סוֹבֵב sôbēb) を使う
HOLLOW_STEMS = {'piel': [('polel', 'o')], 'pual': [('polal', 'O')], 'hithpael': [('hithpolel', 'r')]}
GEMINATE_STEMS = {'piel': [('piel', 'p'), ('poel', 'm')], 'pual': [('pual', 'P'), ('poal', 'M')],
                  'hithpael': [('hithpael', 't'), ('hithpoel', 'z')]}


def _hollow(root):
    root = _plain(root)
    return len(root) == 3 and root[1] in 'וי'


def _geminate(root):
    root = _plain(root)
    return len(root) == 3 and root[1] == root[2]


def _stem_codes(root, stem):
    """[(態の名前, OSHB の符号)] (試す順)"""
    if _hollow(root) and stem in HOLLOW_STEMS:
        return HOLLOW_STEMS[stem]
    if _geminate(root) and stem in GEMINATE_STEMS:
        return GEMINATE_STEMS[stem]
    return [(stem, STEM_CODES[stem])]


def _stem_code(root, stem):
    return _stem_codes(root, stem)[0][1]
# 表の列: (名前, OSHB の時制の型, 人称性数)
COLUMNS = [('完了 3男単', 'qatal', ('p', '3ms')), ('未完了 3男単', 'yiqtol', ('i', '3ms')),
           ('命令 2男単', 'imperative', ('v', '2ms')), ('分詞 男単', 'participle', ('r', 'msa')),
           ('不定詞連語形', 'infinitive', ('c', ''))]
# ラテン文字の語根 (ktb) → ヘブライ文字
LATIN = {'ʾ': 'א', "'": 'א', 'b': 'ב', 'v': 'ב', 'g': 'ג', 'd': 'ד', 'h': 'ה', 'w': 'ו', 'z': 'ז', 'ḥ': 'ח',
         'ṭ': 'ט', 'y': 'י', 'k': 'כ', 'l': 'ל', 'm': 'מ', 'n': 'נ', 's': 'ס', 'ʿ': 'ע', 'p': 'פ', 'f': 'פ',
         'ṣ': 'צ', 'q': 'ק', 'r': 'ר', 'š': 'ש', 'ś': 'ש', 't': 'ת'}


def parse_root(text):
    """語根の入力 (כתב / ktb / 語形 וַיִּכְתֹּב) → 語根の3字 (子音だけ)"""
    text = text.strip()
    if script.is_hebrew(text):
        letters = script.consonants(text)
        if len(letters) <= 3:
            return ''.join(script.FINALS.get(c, c) for c in letters)
        # 語形なら OSHB の解析から語根を引く
        for analysis in dictionary.forms(text):
            for lemma, code in zip(analysis['lemmas'], analysis['morph'][1:].split('/')):
                entry = dictionary.lexicon(lemma) if code.startswith('V') else None
                if entry and entry.get('root'):
                    return script.consonants(entry['root'])
        return letters
    return ''.join(LATIN.get(c, '') for c in text.lower() if c not in '-. ')


def weak(root):
    """作った形が実際と違いうる語根か (喉音・弱い字)。理由の文字列 (無ければ '')"""
    reasons = []
    if any(c in GUTTURALS for c in root):
        reasons.append('喉音・ר を含む')
    if root[:1] in 'ניו':
        reasons.append('1字目が %s' % root[0])
    if root[1:2] in 'וי':
        reasons.append('2字目が %s' % root[1])
    if root[2:3] in 'הא':
        reasons.append('3字目が %s' % root[2])
    if len(root) == 3 and root[1] == root[2]:
        reasons.append('2字目と3字目が同じ')
    return '、'.join(reasons)


def generate(root, stem, column):
    """強い語根の型から形を作る (母音記号付き)。型が無ければ None。
    弱いダゲシュは begadkefat の字が語頭か、黙字のシェヴァ (閉じた音節 נִכְ|תַּב) の後ろにあるときに付ける"""
    template = TEMPLATES.get(stem, {}).get(column)
    if template is None or len(root) != 3:
        return None
    if stem == 'hithpael' and root[0] in SIBILANTS:
        template = _metathesis(template, root[0])
    # 黙字のシェヴァ: 母音のある字の後ろのシェヴァ (語頭のシェヴァ、シェヴァの後ろのシェヴァは有声)
    silent = [vowel == 'sheva' and i > 0 and template[i - 1][1] not in ('', 'sheva')
              for i, (_, vowel, _) in enumerate(template)]
    out = []
    for i, (slot, vowel, dagesh) in enumerate(template):
        letter = root[slot - 1] if isinstance(slot, int) else slot
        letter = script.FINALS.get(letter, letter)
        if i == len(template) - 1:
            letter = FINAL.get(letter, letter)
        marks = SHIN_DOT if letter == 'ש' else ''
        if dagesh == 'F' and letter not in GUTTURALS:
            marks += DAGESH
        elif dagesh == 'L' and letter in BGDKPT and (i == 0 or silent[i - 1]):
            marks += DAGESH
        if letter == 'ך' and not vowel:
            vowel = 'sheva'  # 語末の ך にはシェヴァを書く (מָלַךְ)
        out.append(letter + marks + (POINT['hiriq'] + 'י' if vowel == 'yod' else POINT[vowel]))
    return _sin(root, unicodedata.normalize('NFC', ''.join(out)))  # 記号の並び (ダゲシュと母音記号) を正規の順に


SIBILANTS = {'ס': 'ת', 'ש': 'ת', 'צ': 'ט', 'ז': 'ד'}


def _metathesis(template, first):
    """hithpael の ת と、歯擦音の1字目を入れ替える (hit-šammēr → hištammēr、צ の後ろの ת は ט、ז の後ろは ד)"""
    out = list(template)
    t = next(i for i, part in enumerate(out) if part[0] == 'ת')
    r1 = next(i for i, part in enumerate(out) if part[0] == 1)
    out[t], out[r1] = (1, out[t][1], ''), (SIBILANTS[first], out[r1][1], 'L')  # 入れ替えた ת は黙字のシェヴァの後ろ
    return out


def attested(forms, stem, column, root=''):
    """OSHB に現れた形のうち、その態・型・人称性数のもの。接頭辞・人称接尾辞の付いていない語の形を優先し、
    人称接尾辞の付いた語 (形が欠ける) は使わない。(形, 回数, 注記) / None"""
    vtype, pgn = dict((c[1], c[2]) for c in COLUMNS)[column]
    for _, code in _stem_codes(root, stem):
        bare = [f for f in forms if f['stem'] == code and f['type'] == vtype and f['pgn'] == pgn
                and f['lang'] == 'H' and f['bare']]
        if bare:
            # 語頭の begadkefat に弱いダゲシュのある形を優先 (前の語が母音で終わると落ちる: דָרַשׁ / דָּרַשׁ)
            with_lene = [f for f in bare if _initial_lene(f['form'])]
            best = with_lene[0] if with_lene else bare[0]
            return best['form'], best['count'], None
        if column == 'yiqtol':
            # 連続未完了 (וַיִּכְתֹּב) の動詞の部分は、接頭の字の強いダゲシュを除けば未完了と同じ形
            matches = [f for f in forms if f['stem'] == code and f['type'] == 'w' and f['pgn'] == '3ms'
                       and f['lang'] == 'H' and len(f['form']) > 2]
            if matches:
                return _undouble_prefix(matches[0]['form']), matches[0]['count'], 'wayyiqtol'
    return None


# ----------------------------------------------------------------------
# 弱い語根・喉音を含む語根: 同じ分類の別の語根で聖書に現れた形から類推する
#
#   נפל の hiphil 完了 (聖書に無い) ← 同じ I-נ の נגד の הִגִּיד → הִפִּיל
#
# 分類は字の位置ごと: נ (1字目)、ו・י、א、ה、喉音 ח ע、ר、2字目と3字目が同じ (重複語根)。それ以外は強い字

# 不規則な動詞 (類推の材料にしない): הלך は I-י のように、לקח は I-נ のように振る舞う。היה・חיה は独特
IRREGULAR = {'הלכ', 'לקח', 'היה', 'חיה', 'נתנ'}  # 語末形を普通の形にした語根


def _plain(root):
    """語末形の字を普通の形に (נתץ → נתצ)"""
    return ''.join(script.FINALS.get(c, c) for c in root)


def signature(root):
    """語根の分類 (字の位置ごと)"""
    root = _plain(root)
    out = []
    for i, c in enumerate(root):
        if i == 2 and len(root) == 3 and root[1] == root[2]:
            out.append('=')
        elif c == 'נ' and i == 0:
            out.append('n')
        elif c in 'וי':
            out.append('wy' if i == 0 else c)  # 1字目の ו・י はほぼ同じ振る舞い (ישב, ולד → ילד)
        elif c in 'אה':
            out.append(c)
        elif c in 'חע':
            out.append('g')
        elif c == 'ר':
            out.append('r')
        else:
            out.append('')
    return tuple(out)


def _relaxed(sig):
    """分類を少しゆるめる (喉音 א ה ח ע・ר を1字目と2字目では同じ扱いに)"""
    return tuple('G' if i < 2 and x in ('א', 'ה', 'g', 'r') else x for i, x in enumerate(sig))


# 分類をゆるめるときに無視する順: 形への影響の小さい性質から (喉音・ר → 1字目の נ・י → 3字目の א → 3字目の ה → 2字目の ו・י・重複)
IMPORTANCE = {'g': 1, 'r': 1, 'G': 1, 'n': 3, 'wy': 3, '=': 5}


def _importance(i, x):
    if x == 'א':
        return 3.5 if i == 2 else 1
    if x == 'ה':
        return 4 if i == 2 else 1
    if x in ('ו', 'י'):
        return 5
    return IMPORTANCE.get(x, 0)


def _backoff(sig):
    """分類を段階的にゆるめた列: そのまま → 喉音を同じ扱いに → 影響の小さい性質から1つずつ無視 → 2つ無視。
    すべて強い字になるもの (強い語根の型と同じ) は除く (יצא: I-י + III-א → III-א だけの מָצָא から。
    בוא: II-ו + III-א → II-ו だけの קָם から)"""
    out = [sig, _relaxed(sig)]
    weak = sorted((i for i, x in enumerate(sig) if x), key=lambda i: _importance(i, sig[i]))
    masks = [(i,) for i in weak] + [(i, j) for n, i in enumerate(weak) for j in weak[n + 1:]]
    for masked in masks:
        candidate = tuple('' if i in masked else x for i, x in enumerate(sig))
        out += [candidate, _relaxed(candidate)]
    return [x for x in dict.fromkeys(out) if any(x)]


_donors = None


def donors():
    """(分類, 態, 型, 人称性数) → [(語根, 形, 回数)] (回数の多い順)"""
    global _donors
    if _donors is None:
        _donors = {}
        for root, stem, vtype, pgn, form, count in dictionary.bare_verb_forms():
            root = _plain(root)
            if root in IRREGULAR or len(root) != 3:
                continue
            # 借りる側の語根自身の分類 (と喉音をまとめた分類) だけに登録する。ゆるめるのは探す側 (_backoff)
            for sig in {signature(root), _relaxed(signature(root))}:
                _donors.setdefault((sig, stem, vtype, pgn), []).append((root, form, count))
        for key in _donors:
            _donors[key].sort(key=lambda r: -r[2])
    return _donors


def _clusters(form):
    """[[字, 記号の列]]"""
    out = []
    for c in unicodedata.normalize('NFD', form):
        if '\u05d0' <= c <= '\u05ea':
            out.append([c, ''])
        elif out:
            out[-1][1] += c
    return out


def _align(letters, root):
    """形の字の列と語根の3字の対応: 語根の字 i → 形の字の位置 (無ければ None)。合う字の数が多く、
    3字目が最後の字に来るものを選ぶ (יִתֵּן: נ は3字目)"""
    base = [script.FINALS.get(c, c) for c in letters]
    best, best_score = None, None

    def walk(i, start, chosen):
        nonlocal best, best_score
        if i == len(root):
            matched = sum(x is not None for x in chosen)
            # 合う字の数、3字目が最後の字か、2字目が合うか、前寄りか (הוֹבִישׁ の י は母音の字で、1字目ではない)
            score = (matched, chosen[-1] == len(base) - 1, chosen[1] is not None,
                     -sum(x for x in chosen if x is not None))
            if best_score is None or score > best_score:
                best, best_score = list(chosen), score
            return
        walk(i + 1, start, chosen + [None])
        for j in range(start, len(base)):
            if base[j] == root[i]:
                walk(i + 1, j + 1, chosen + [j])
    walk(0, 0, [])
    return best


def _lene_context(clusters, j):
    """j の字が弱いダゲシュの位置か (語頭、または黙字のシェヴァの後ろ)"""
    if j == 0:
        return True
    prev = clusters[j - 1][1]
    return '\u05b0' in prev and not any(v in clusters[j - 2][1] for v in '\u05b0') if j >= 2 else '\u05b0' in prev


def substitute(form, donor_root, root):
    """借りた形の語根の字を入れ替える。合わなければ None"""
    donor_root, root = _plain(donor_root), _plain(root)
    clusters = _clusters(form)
    positions = _align([c for c, _ in clusters], donor_root)
    if positions is None or sum(p is not None for p in positions) < 2:
        return None
    for i, j in enumerate(positions):
        if j is None:
            continue
        letter, marks = root[i], clusters[j][1]
        marks = marks.replace(SHIN_DOT, '').replace('\u05c2', '')
        donor = donor_root[i]
        has_dagesh = DAGESH in marks
        lene = _lene_context(clusters, j)
        if has_dagesh and (letter in GUTTURALS or (lene and letter not in BGDKPT)):
            marks = marks.replace(DAGESH, '')  # 喉音は重ねない、begadkefat でない字に弱いダゲシュは付かない
        elif not has_dagesh and lene and letter in BGDKPT and donor not in BGDKPT:
            marks = DAGESH + marks
        if letter == 'ש':
            marks = SHIN_DOT + marks
        if j == len(clusters) - 1:
            letter = FINAL.get(letter, letter)
            marks = marks.replace('\u05b0', '')
            if letter == 'ך':
                marks += '\u05b0'  # 語末の ך にはシェヴァを書く
        clusters[j] = [letter, marks]
    # 重ねた3字目 (polel の כּוֹנֵן、קוֹמֵם) も入れ替える: 2字目より後ろの、借りた語根の3字目と同じ字
    after = max([p for p in positions[:2] if p is not None], default=-1)
    for k in range(after + 1, len(clusters)):
        if k not in positions and script.FINALS.get(clusters[k][0], clusters[k][0]) == donor_root[2]:
            letter = root[2]
            marks = clusters[k][1].replace(SHIN_DOT, '').replace('\u05c2', '')
            if letter == 'ש':
                marks = SHIN_DOT + marks
            clusters[k] = [FINAL.get(letter, letter) if k == len(clusters) - 1 else letter, marks]
    return _sin(root, unicodedata.normalize('NFC', ''.join(c + m for c, m in clusters)))


_sin_roots = {}


def _sin(root, form):
    """語根の ש が שׂ (sin) なら形の ש の点を ׂ に (עָשָׂה)。語根の聖書の形から判定する"""
    root = _plain(root)
    if 'ש' not in root:
        return form
    if root not in _sin_roots:
        forms = [f['form'] for f in dictionary.verb_forms(root)]
        sin = sum('\u05c2' in unicodedata.normalize('NFD', f) for f in forms)
        shin = sum(SHIN_DOT in unicodedata.normalize('NFD', f) for f in forms)
        _sin_roots[root] = sin > shin
    if _sin_roots[root]:
        form = unicodedata.normalize('NFC', unicodedata.normalize('NFD', form).replace(SHIN_DOT, '\u05c2'))
    return form


def analogize(root, stem, column):
    """同じ分類の別の語根の形から類推する。(形, 借りた語根) / None"""
    vtype, pgn = dict((c[1], c[2]) for c in COLUMNS)[column]
    for _, code in _stem_codes(root, stem):
        # 分類の近い順に、分類ごとに借りる語根を VOTERS 個まで集めて、作った形で多数決 (語根ごとの癖
        # (状態動詞の母音 מָלֵא、יָרֵא) を写さないように)。借りる語根が MIN_VOTERS 個に満たなければ次の分類も足す
        votes, first_donor, used = {}, {}, set()
        for sig in _backoff(signature(root)):
            level_used = 0
            for donor_root, form, count in donors().get((sig, code, vtype, pgn), []):
                if donor_root == _plain(root) or donor_root in used:
                    continue
                made = substitute(form, donor_root, root)
                if not made:
                    continue
                used.add(donor_root)
                level_used += 1
                votes[made] = votes.get(made, 0) + 1  # 回数で重みを付けるより1語根1票のほうが当たる (評価で確かめた)
                first_donor.setdefault(made, donor_root)
                if level_used >= VOTERS:
                    break
            if len(used) >= MIN_VOTERS:
                break
        if votes:
            order = list(first_donor)
            made = max(votes, key=lambda m: (votes[m], -order.index(m)))
            return made, first_donor[made]
    return None


VOTERS = 9
MIN_VOTERS = 1


def _initial_lene(form):
    nfd = unicodedata.normalize('NFD', form)
    return not nfd or nfd[0] not in BGDKPT or DAGESH in nfd[1:4]


def _undouble_prefix(form):
    """連続未完了の接頭の字の強いダゲシュを除く (יִּכְתֹּב → יִכְתֹּב)"""
    if len(form) > 1 and form[1] == DAGESH:
        return form[0] + form[2:]
    return form


def table(root_text):
    """態の型の表 (表示用の行のリスト)"""
    root = parse_root(root_text)
    if len(root) != 3:
        return ['語根は3字で (例: כתב / ktb): %s' % root_text]
    forms = dictionary.verb_forms(root)
    lemmas = {f['lemma'] for f in forms if f['lang'] == 'H'}  # アラム語の見出し語は除く
    glosses = [dictionary.lexicon(l) for l in sorted(lemmas)]
    lines = ['語根 %s' % explain.root_text(root)]
    for entry in glosses:
        if entry:
            lines.append('  %s %s: %s' % (entry['xlit'], script.isolate(entry['word']), entry['ja']))
    reason = weak(root)
    if reason:
        lines.append('  (%s語根: * の形は規則どおりに作ったもので、実際とは違うことがある)' % reason)
    used = {f['stem'] for f in forms if f['lang'] == 'H'}
    for stem in STEMS:
        modern, kana, desc = explain.BINYANIM[stem]
        mark = '' if any(c in used for _, c in _stem_codes(root, stem)) else '  (聖書に無い態)'
        lines.append('')
        names = _stem_codes(root, stem)
        if names[0][0] != stem or len(names) > 1:
            used_names = [n for n, c in names if c in used] or [names[0][0]]
            lines.append('%s (この語根の %s): %s%s' % (' / '.join(used_names), stem, desc, mark))
        else:
            lines.append('%s (%s %s): %s%s' % (stem, modern, kana, desc, mark))
        for label, column, _ in COLUMNS:
            found = attested(forms, stem, column, root)
            if found:
                form, count, note = found
                lines.append('    %-12s   %-14s %s ×%d%s' % (label, script.translit(form), script.isolate(form), count,
                                                             ' (連続未完了の形から)' if note else ''))
            else:
                guess = analogize(root, stem, column) if signature(root) != ('', '', '') else None
                if guess is None and (_hollow(root) and stem in HOLLOW_STEMS or _geminate(root) and stem in GEMINATE_STEMS):
                    continue  # polel・poel の型は作らない (piel の型は合わない)
                if guess:
                    form, donor = guess
                    lines.append('    %-12s † %-14s %s (%s から類推)' % (label, script.translit(form), script.isolate(form),
                                                                   script.isolate(script.with_final(donor))))
                    continue
                form = generate(root, stem, column)
                if form:
                    lines.append('    %-12s * %-14s %s' % (label, script.translit(form), script.isolate(form)))
    lines.append('')
    lines.append('(×の数は聖書 (OSHB) での出現回数。† は聖書に無い形を、同じ分類 (弱い字・喉音の位置) の別の語根の形から類推したもの、')
    lines.append(' * は強い語根の型から作ったもの)')
    return lines
