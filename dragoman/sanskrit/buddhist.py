#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 仏教梵語の語彙 (漢訳語)
#
# Wiktionary の訳語は一般の意味 (śāri「チェスの駒」、śruta「筒抜け」) なので、仏典によく出る語は漢訳の訳語を先に使う。
# 見出し (語幹、IAST) → (訳語, 品詞)。dictionary.lemmas がこの表を先に返すので、語の訳語・複合語の分解
# (prajñāpāramitā → prajñā + pāramitā)・複合語の要素の訳語のどれにも効く。
#
from . import script

TERMS = {
    # 仏・菩薩・人
    'buddha': ('仏', 'noun'), 'bodhisattva': ('菩薩', 'noun'), 'mahāsattva': ('摩訶薩', 'noun'),
    'bhagavat': ('世尊', 'noun'), 'tathāgata': ('如来', 'noun'), 'arhat': ('阿羅漢', 'noun'),
    'samyaksaṃbuddha': ('正等覚者', 'noun'), 'bhikṣu': ('比丘', 'noun'), 'bhikṣuṇī': ('比丘尼', 'noun'),
    'śrāvaka': ('声聞', 'noun'), 'pratyekabuddha': ('独覚', 'noun'), 'saṃgha': ('僧伽', 'noun'),
    'avalokiteśvara': ('観自在', 'name'), 'āryāvalokiteśvara': ('聖観自在', 'name'), 'ārya': ('聖', 'adj'),
    'śāriputra': ('舎利子', 'name'), 'śāradvatīputra': ('舎利子', 'name'), 'ānanda': ('阿難', 'name'),
    'mañjuśrī': ('文殊', 'name'), 'maitreya': ('弥勒', 'name'), 'subhūti': ('須菩提', 'name'),
    'kulaputra': ('善男子', 'noun'), 'kuladuhitṛ': ('善女人', 'noun'), 'āyuṣmat': ('具寿', 'noun'),
    'deva': ('天', 'noun'), 'mānuṣa': ('人', 'noun'), 'asura': ('阿修羅', 'noun'), 'gandharva': ('乾闥婆', 'noun'),
    'nāga': ('龍', 'noun'), 'yakṣa': ('夜叉', 'noun'), 'parṣad': ('会衆', 'noun'), 'loka': ('世間', 'noun'),
    # 場所・時
    'rājagṛha': ('王舎城', 'name'), 'gṛdhrakūṭa': ('霊鷲山', 'name'), 'jetavana': ('祇園', 'name'),
    'śrāvastī': ('舎衛城', 'name'), 'samaya': ('時', 'noun'), 'tryadhvan': ('三世', 'noun'),
    # 経・教え
    'sūtra': ('経', 'noun'), 'dharma': ('法', 'noun'), 'dharmaparyāya': ('法門', 'noun'), 'mantra': ('呪', 'noun'),
    'vidyā': ('明', 'noun'), 'avidyā': ('無明', 'noun'), 'hṛdaya': ('心', 'noun'), 'bhāṣita': ('所説', 'noun'),
    'śruta': ('聞いた', 'adj'), 'yāna': ('乗', 'noun'), 'mahāyāna': ('大乗', 'noun'),
    # 般若
    'prajñā': ('般若', 'noun'), 'pāramitā': ('波羅蜜多', 'noun'), 'prajñāpāramitā': ('般若波羅蜜多', 'noun'),
    'caryā': ('行', 'noun'), 'gambhīra': ('甚深の', 'adj'), 'samādhi': ('三昧', 'noun'),
    'śūnya': ('空の', 'adj'), 'śūnyatā': ('空性', 'noun'), 'svabhāva': ('自性', 'noun'),
    'svabhāvaśūnya': ('自性空の', 'adj'), 'lakṣaṇa': ('相', 'noun'),
    # 五蘊・十二処・十八界
    'skandha': ('蘊', 'noun'), 'rūpa': ('色', 'noun'), 'vedanā': ('受', 'noun'), 'saṃjñā': ('想', 'noun'),
    'saṃskāra': ('行', 'noun'), 'vijñāna': ('識', 'noun'),
    'cakṣus': ('眼', 'noun'), 'śrotra': ('耳', 'noun'), 'ghrāṇa': ('鼻', 'noun'), 'jihvā': ('舌', 'noun'),
    'kāya': ('身', 'noun'), 'manas': ('意', 'noun'), 'śabda': ('声', 'noun'), 'gandha': ('香', 'noun'),
    'rasa': ('味', 'noun'), 'spraṣṭavya': ('触', 'noun'), 'dhātu': ('界', 'noun'), 'āyatana': ('処', 'noun'),
    'manovijñāna': ('意識', 'noun'), 'cakṣurdhātu': ('眼界', 'noun'), 'manodhātu': ('意界', 'noun'),
    'manovijñānadhātu': ('意識界', 'noun'), 'dharmadhātu': ('法界', 'noun'),
    # 十二縁起・四諦
    'jarāmaraṇa': ('老死', 'noun'), 'jarā': ('老', 'noun'), 'maraṇa': ('死', 'noun'), 'kṣaya': ('尽', 'noun'),
    'duḥkha': ('苦', 'noun'), 'samudaya': ('集', 'noun'), 'nirodha': ('滅', 'noun'), 'mārga': ('道', 'noun'),
    'jñāna': ('智', 'noun'), 'prāpti': ('得', 'noun'), 'aprāpti': ('無得', 'noun'), 'aprāptitva': ('無所得', 'noun'),
    # 不生不滅 …
    'anutpanna': ('不生の', 'adj'), 'aniruddha': ('不滅の', 'adj'), 'amala': ('不垢の', 'adj'),
    'vimala': ('離垢の', 'adj'), 'ūna': ('減った', 'adj'), 'anūna': ('不減の', 'adj'),
    'paripūrṇa': ('満ちた', 'adj'), 'asaṃpūrṇa': ('不増の', 'adj'),
    # 心無罣礙 …
    'citta': ('心', 'noun'), 'āvaraṇa': ('罣礙', 'noun'), 'cittāvaraṇa': ('心の罣礙', 'noun'),
    'acittāvaraṇa': ('心に罣礙の無い', 'adj'), 'trasta': ('恐怖した', 'adj'), 'atrasta': ('恐怖の無い', 'adj'),
    'viparyāsa': ('顛倒', 'noun'), 'atikrānta': ('遠離した', 'adj'), 'viparyāsātikrānta': ('顛倒を遠離した', 'adj'),
    'niṣṭhā': ('究竟', 'noun'), 'nirvāṇa': ('涅槃', 'noun'), 'niṣṭhanirvāṇa': ('究竟涅槃に至った', 'adj'),
    'vyavasthita': ('住する', 'adj'), 'anuttara': ('無上の', 'adj'), 'samyaksaṃbodhi': ('正等覚', 'noun'),
    'anuttarā samyaksaṃbodhi': ('阿耨多羅三藐三菩提', 'noun'), 'abhisaṃbuddha': ('現等覚した', 'adj'),
    'bodhi': ('菩提', 'noun'),
    # 呪
    'mahāmantra': ('大呪', 'noun'), 'mahāvidyāmantra': ('大明呪', 'noun'), 'anuttaramantra': ('無上呪', 'noun'),
    'asamasamamantra': ('無等等呪', 'noun'), 'praśamana': ('除くもの', 'noun'),
    'sarvaduḥkhapraśamana': ('能除一切苦', 'adj'), 'satya': ('真実', 'noun'), 'amithyātva': ('不虚', 'noun'),
    'svāhā': ('薩婆訶', 'interj'), 'pāragata': ('彼岸に往った', 'adj'), 'pārasaṃgata': ('彼岸に完全に往った', 'adj'),
    # 称賛・歓喜
    'sādhu': ('善哉', 'interj'), 'sādhukāra': ('善哉の声', 'noun'), 'ānandamanas': ('歓喜した', 'adj'),
    'āttamanas': ('歓喜した', 'adj'),
}

# 動詞 (接頭辞つきの語根、IAST。vidyut の解析の語根) → 訳語
VERBS = {'vyavaloki': '観察する', 'vyavalok': '観察する', 'avalok': '観る', 'vihṛ': '住する', 'abhinand': '歓喜する',
         'samanupaś': '観察する', 'samanudṛś': '観察する', 'abhisaṃbudh': '現等覚する', 'śikṣ': '学ぶ',
         'anumud': '随喜する', 'āśri': '依る', 'samāpad': '入る', 'vyutthā': '出る', 'nirdiś': '説く'}

# 仏典らしい語 (SLP1)。文章にこれがあれば表を使う (自動。--buddhist / --no-buddhist で決められる)
# (bhagavat・nirvāṇa・arhat はヒンドゥーのテキストにも出る (Gītā の bhagavān、brahmanirvāṇa、arhati「値する」) ので入れない)
MARKERS = ('boDisattva', 'SAriputra', 'SAradvatIputra', 'prajYApAramit', 'tATAgata', 'avalokiteSvara',
           'samyaksaMboDi', 'kulaputra', 'saMbudDa', 'samyaksaMbudDa', 'pratyekabudDa', 'SrAvaka')
FORCED = None    # None: 自動、True / False: 指定
_active = False
_by_slp1 = None


def set_forced(flag):
    global FORCED
    FORCED = flag


def detect(text):
    """文章ごとに、仏典の語彙の表を使うか決める"""
    slp1 = script.to_slp1(text)
    set_active(FORCED if FORCED is not None else any(m in slp1 for m in MARKERS))


def set_active(flag):
    global _active
    if flag != _active:
        _active = flag
        from . import compound
        compound.split.cache_clear()  # 複合語の分け方は訳語の表で変わる


def active():
    return _active


def lemmas(key):
    """見出し (SLP1) → dictionary.lemmas と同じ形の項目 (表に無いか、使わないときは空)"""
    global _by_slp1
    if not _active:
        return []
    if _by_slp1 is None:
        _by_slp1 = {}
        for k, (ja, pos) in TERMS.items():
            _by_slp1[script.to_slp1(k)] = (ja, pos)
            if pos == 'adj' and k.endswith('a'):
                _by_slp1.setdefault(script.to_slp1(k[:-1] + 'ā'), (ja, pos))  # 女性形 (amalā)
    if key not in _by_slp1:
        return []
    ja, pos = _by_slp1[key]
    return [{'pos': pos, 'ja': ja, 'gloss_lang': 'ja', 'word': script.iast(key), 'gana': None, 'causative': False,
             'senses': 100, 'buddhist': True}]


def patch_verbs(items):
    """動詞・分詞の訳語を表の訳語に (vyavalokayati → 観察する)"""
    if not _active:
        return items
    for item in items:
        if item.get('pos') in ('verb', 'participle') and item.get('pres1sg') in VERBS:
            item['ja'], item['gloss_lang'] = VERBS[item['pres1sg']], 'ja'
        elif item.get('pos') in ('noun', 'adj', 'name') and _term(item.get('base')):
            item['ja'], item['gloss_lang'] = _term(item['base'])[0], 'ja'  # 語根からの名詞 (saṃjñā「想」)
    # 表の名詞を先に (saṃjñā: 名詞「想」を、動詞の読みより)
    in_table = lambda item: item.get('pos') in ('noun', 'adj', 'name') and _term(item.get('base'))
    return sorted(items, key=lambda item: not in_table(item))


def _term(base):
    """表の見出し (語幹の -a / -ā の違いも: vedana → vedanā「受」)"""
    if not base:
        return None
    for key in (base, base + 'ā' if base.endswith('a') else None, base[:-1] + 'a' if base.endswith('ā') else None):
        if key in TERMS:
            return TERMS[key]
    return None
