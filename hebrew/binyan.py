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
        out.append(letter + marks + (POINT['hiriq'] + 'י' if vowel == 'yod' else POINT[vowel]))
    return unicodedata.normalize('NFC', ''.join(out))  # 記号の並び (ダゲシュと母音記号) を正規の順に


SIBILANTS = {'ס': 'ת', 'ש': 'ת', 'צ': 'ט', 'ז': 'ד'}


def _metathesis(template, first):
    """hithpael の ת と、歯擦音の1字目を入れ替える (hit-šammēr → hištammēr、צ の後ろの ת は ט、ז の後ろは ד)"""
    out = list(template)
    t = next(i for i, part in enumerate(out) if part[0] == 'ת')
    r1 = next(i for i, part in enumerate(out) if part[0] == 1)
    out[t], out[r1] = (1, out[t][1], ''), (SIBILANTS[first], out[r1][1], 'L')  # 入れ替えた ת は黙字のシェヴァの後ろ
    return out


def attested(forms, stem, column):
    """OSHB に現れた形のうち、その態・型・人称性数のもの。接頭辞・人称接尾辞の付いていない語の形を優先し、
    人称接尾辞の付いた語 (形が欠ける) は使わない。(形, 回数, 注記) / None"""
    vtype, pgn = dict((c[1], c[2]) for c in COLUMNS)[column]
    code = STEM_CODES[stem]

    def pick(vt, pg):
        matches = [f for f in forms if f['stem'] == code and f['type'] == vt and f['pgn'] == pg and f['lang'] == 'H']
        bare = [f for f in matches if f['bare']]
        return bare[0] if bare else None
    found = pick(vtype, pgn)
    if found:
        return found['form'], found['count'], None
    if column == 'yiqtol':
        # 連続未完了 (וַיִּכְתֹּב) の動詞の部分は、接頭の字の強いダゲシュを除けば未完了と同じ形
        matches = [f for f in forms if f['stem'] == code and f['type'] == 'w' and f['pgn'] == '3ms'
                   and f['lang'] == 'H' and len(f['form']) > 2]
        if matches:
            return _undouble_prefix(matches[0]['form']), matches[0]['count'], 'wayyiqtol'
    return None


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
        mark = '' if STEM_CODES[stem] in used else '  (聖書に無い態)'
        lines.append('')
        lines.append('%s (%s %s): %s%s' % (stem, modern, kana, desc, mark))
        for label, column, _ in COLUMNS:
            found = attested(forms, stem, column)
            if found:
                form, count, note = found
                lines.append('    %-12s   %-14s %s ×%d%s' % (label, script.translit(form), script.isolate(form), count,
                                                             ' (連続未完了の形から)' if note else ''))
            else:
                form = generate(root, stem, column)
                if form:
                    lines.append('    %-12s * %-14s %s' % (label, script.translit(form), script.isolate(form)))
    lines.append('')
    lines.append('(* は聖書 (OSHB) に無い形を、強い語根の型から作ったもの。×の数は聖書での出現回数)')
    return lines
