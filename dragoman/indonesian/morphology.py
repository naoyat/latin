#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# インドネシア語・マレー語の語形の解析
#
# 語形変化は無く、派生の接辞と接語で語を作る。辞書 (Wiktionary) に載っている形はそのまま引き、無ければ接辞を外して
# 語根を引く:
#   接語    -nya (彼の / その)、-ku (私の)、-mu (あなたの)、-lah (強調)、-kah (疑問)、-pun (〜も)
#   接尾辞  -kan (使役・他動)、-i (場所・反復の他動)、-an (名詞)
#   接頭辞  meN- (能動の他動詞。鼻音が語根の頭と交替: menulis ← tulis、memakan ← makan、menyapu ← sapu、
#           mengirim ← kirim、membaca ← baca、mendengar ← dengar、melihat ← lihat、mengecat ← cat)
#           di- (受動)、ber- (自動詞・〜を持つ)、ter- (偶発・状態・最上級)、memper- / diper- (使役)、se- (一つの・同じ)
#   接周辞  ke-…-an (抽象名詞: kebersihan ← bersih)、pe(N)-…-an (行為の名詞)、per-…-an、pe(N)- (〜する人: penulis)
#   重複    anak-anak (複数)、kata-kata
#
import functools
import re

from . import dictionary

GENDER = 'c'
CASES = ('Nom', 'Acc', 'Gen')

PRONOUNS = {'saya': ('私', 1, 'sg'), 'aku': ('私', 1, 'sg'), 'kamu': ('あなた', 2, 'sg'), 'engkau': ('あなた', 2, 'sg'),
            'anda': ('あなた', 2, 'sg'), 'dia': ('彼', 3, 'sg'), 'ia': ('彼', 3, 'sg'), 'beliau': ('あの方', 3, 'sg'),
            'kami': ('私たち', 1, 'pl'), 'kita': ('私たち', 1, 'pl'), 'mereka': ('彼ら', 3, 'pl'),
            'kalian': ('あなたたち', 2, 'pl'), 'awak': ('あなた', 2, 'sg'), 'ini': ('これ', 3, 'sg'),
            'itu': ('それ', 3, 'sg'), 'siapa': ('誰', 3, 'sg'), 'apa': ('何', 3, 'sg')}
CLITICS = {'nya': ('彼の', 3), 'ku': ('私の', 1), 'mu': ('あなたの', 2)}
PARTICLE_CLITICS = {'lah': '', 'kah': 'か', 'pun': 'も'}
DEMONSTRATIVES = {'ini': ('この', 'これ'), 'itu': ('その', 'それ'), 'tersebut': ('その', 'それ')}
# 名詞の前に置く語 (数量詞・複数の標識)
PRENOMINAL = {'semua': 'すべての', 'banyak': '多くの', 'beberapa': 'いくつかの', 'para': '', 'setiap': 'それぞれの',
              'tiap': 'それぞれの', 'segala': 'あらゆる', 'seluruh': '全体の', 'sedikit': '少しの', 'berbagai': 'さまざまな',
              'sebuah': 'ある', 'seorang': 'ある', 'seekor': 'ある', 'satu': '一つの', 'dua': '二つの', 'tiga': '三つの',
              'empat': '四つの', 'lima': '五つの', 'para': ''}
PREPOSITIONS = {'di': 'で', 'ke': 'へ', 'dari': 'から', 'pada': 'に', 'kepada': 'に', 'untuk': 'のために',
                'bagi': 'にとって', 'dengan': 'と', 'oleh': 'によって', 'tentang': 'について', 'dalam': 'の中で',
                'seperti': 'のように', 'antara': 'の間で', 'sejak': 'から', 'sampai': 'まで', 'hingga': 'まで',
                'tanpa': 'なしに', 'menurut': 'によれば', 'terhadap': 'に対して', 'akan': None, 'atas': 'の上に',
                'bersama': 'とともに', 'daripada': 'より', 'demi': 'のために', 'melalui': 'を通じて',
                'mengenai': 'について', 'kecuali': '以外'}
CONJUNCTIONS = {'dan': 'そして,〜と', 'atau': 'または', 'tetapi': 'しかし', 'tapi': 'しかし', 'namun': 'しかし',
                'karena': '〜なので', 'kerana': '〜なので', 'sebab': '〜なので', 'jika': 'もし', 'kalau': 'もし',
                'apabila': '〜するとき', 'ketika': '〜するとき', 'waktu': '〜するとき', 'saat': '〜するとき',
                'bahwa': '〜ということ', 'bahawa': '〜ということ', 'supaya': '〜するように', 'agar': '〜するように',
                'sehingga': 'その結果', 'meskipun': '〜けれども', 'walaupun': '〜けれども', 'serta': 'および',
                'lalu': 'それから', 'kemudian': 'それから', 'yang': None}
# 時制・相の副詞 (後ろの動詞の時制に)、否定
ASPECTS = {'sudah': 'perfect', 'telah': 'perfect', 'akan': 'future', 'sedang': 'progressive',
           'tengah': 'progressive', 'masih': 'still', 'pernah': 'experience'}
NEGATIONS = {'tidak', 'tak', 'bukan', 'belum', 'jangan', 'tiada'}
# 引用の後ろの報告の動詞 (…, kata dia「…と彼は言った」): 後ろの名詞が主語
REPORTING = {'kata': '言う', 'ujar': '言う', 'tutur': '語る', 'ungkap': '明かす', 'jelas': '説明する', 'tambah': '付け加える',
             'imbuh': '付け加える', 'lanjut': '続ける', 'papar': '述べる', 'terang': '説明する', 'katanya': '言う'}
COPULAS = {'adalah': 'である', 'ialah': 'である', 'merupakan': 'である', 'menjadi': 'になる'}
ADVERBS = {'sangat': 'とても', 'amat': 'とても', 'sekali': 'とても', 'juga': '〜も', 'lagi': 'さらに', 'hanya': '〜だけ',
           'saja': '〜だけ', 'sahaja': '〜だけ', 'sering': 'よく', 'selalu': 'いつも', 'kadang-kadang': 'ときどき',
           'sekarang': '今', 'kemarin': '昨日', 'besok': '明日', 'hari ini': '今日', 'di sini': 'ここで',
           'di sana': 'あそこで', 'lebih': 'より', 'paling': '最も', 'terlalu': 'あまりに', 'pula': 'また',
           'segera': 'すぐに'}
# 後ろの動詞と組む語 (mau baca → 読みたい、bisa baca → 読むことができる)
MODALS = {'bisa': 'can', 'dapat': 'can', 'mampu': 'can', 'boleh': 'may', 'harus': 'must', 'mesti': 'must',
          'wajib': 'must', 'mau': 'want', 'ingin': 'want', 'hendak': 'want', 'mahu': 'want', 'perlu': 'need'}
# 訳語を決めておく語 (Wiktionary の最初の語義が外れるもの)
GLOSSES = {'orang': ('人', 'noun'), 'anak': ('子供', 'noun'), 'buku': ('本', 'noun'), 'rumah': ('家', 'noun'),
           'makan': ('食べる', 'verb'), 'minum': ('飲む', 'verb'), 'pergi': ('行く', 'verb'), 'datang': ('来る', 'verb'),
           'baca': ('読む', 'verb'), 'tulis': ('書く', 'verb'), 'lihat': ('見る', 'verb'), 'beri': ('与える', 'verb'),
           'berikan': ('与える', 'verb'), 'ada': ('ある,いる', 'verb'), 'punya': ('持つ', 'verb'), 'tahu': ('知る', 'verb'),
           'sekolah': ('学校', 'noun'), 'guru': ('先生', 'noun'), 'murid': ('生徒', 'noun'), 'nasi': ('ご飯', 'noun'),
           'air': ('水', 'noun'), 'besar': ('大きい', 'adj'), 'kecil': ('小さい', 'adj'), 'baik': ('良い', 'adj'),
           'baru': ('新しい', 'adj'), 'cantik': ('美しい', 'adj'), 'tinggi': ('高い', 'adj'), 'kota': ('町', 'noun'),
           'negara': ('国', 'noun'), 'bahasa': ('言語', 'noun'), 'kucing': ('猫', 'noun'), 'anjing': ('犬', 'noun'),
           'ikan': ('魚', 'noun'), 'ayah': ('父', 'noun'), 'ibu': ('母', 'noun'), 'dokter': ('医者', 'noun'),
           'kerja': ('働く', 'verb'), 'bekerja': ('働く', 'verb'), 'belajar': ('勉強する', 'verb'), 'tidur': ('眠る', 'verb'),
           'mobil': ('車', 'noun'), 'kereta': ('車,列車', 'noun'), 'surat': ('手紙', 'noun'), 'hari': ('日', 'noun'),
           'tahun': ('年', 'noun'), 'waktu': ('時間', 'noun'), 'jalan': ('道', 'noun'), 'pasar': ('市場', 'noun'),
           'uang': ('お金', 'noun'), 'wang': ('お金', 'noun'), 'teman': ('友達', 'noun'), 'kawan': ('友達', 'noun'),
           'rumah sakit': ('病院', 'noun'), 'mahasiswa': ('大学生', 'noun'), 'universitas': ('大学', 'noun'),
           'pemerintah': ('政府', 'noun'), 'presiden': ('大統領', 'noun'), 'masyarakat': ('社会', 'noun'),
           'kami': ('私たち', 'pronoun'), 'lain': ('他の', 'adj'), 'bagus': ('良い', 'adj'), 'senang': ('嬉しい', 'adj'),
           'suka': ('好む', 'verb'), 'cinta': ('愛する', 'verb'), 'tinggal': ('住む', 'verb'), 'beli': ('買う', 'verb'),
           'jual': ('売る', 'verb'), 'cari': ('探す', 'verb'), 'bawa': ('持って行く', 'verb'), 'buat': ('作る', 'verb'),
           'ajar': ('教える', 'verb'), 'masak': ('料理する', 'verb'), 'dengar': ('聞く', 'verb'), 'kirim': ('送る', 'verb'),
           'membangun': ('建設する', 'verb'), 'bangun': ('起きる,建てる', 'verb'), 'meja': ('机', 'noun'),
           'taman': ('公園', 'noun'), 'bermain': ('遊ぶ', 'verb'), 'main': ('遊ぶ', 'verb'),
           'mata uang': ('通貨', 'noun'), 'kereta api': ('列車', 'noun'), 'anak laki-laki': ('男の子', 'noun'),
           'anak perempuan': ('女の子', 'noun'), 'hari raya': ('祝日', 'noun'), 'orang tua': ('親', 'noun'),
           'luar negeri': ('外国', 'noun'), 'dalam negeri': ('国内', 'noun'), 'bank sentral': ('中央銀行', 'noun')}
# 国・地域・言語の名前 (bahasa + 名前 → 〜語)
NAMES = {'indonesia': 'インドネシア', 'jepang': '日本', 'jepun': '日本', 'inggris': 'イギリス', 'inggeris': 'イギリス',
         'belanda': 'オランダ', 'cina': '中国', 'tiongkok': '中国', 'amerika': 'アメリカ', 'jakarta': 'ジャカルタ',
         'malaysia': 'マレーシア', 'arab': 'アラビア', 'jawa': 'ジャワ', 'bali': 'バリ', 'sunda': 'スンダ',
         'melayu': 'マレー', 'prancis': 'フランス', 'perancis': 'フランス', 'jerman': 'ドイツ', 'korea': '韓国',
         'india': 'インド', 'eropa': 'ヨーロッパ', 'asia': 'アジア', 'sumatera': 'スマトラ', 'kalimantan': 'カリマンタン'}
LANGUAGE_NAMES = {'inggris': '英', 'inggeris': '英', 'jepang': '日本', 'jepun': '日本', 'cina': '中国',
                  'arab': 'アラビア', 'belanda': 'オランダ'}
# 場所の前置詞の組 (di atas → の上に)
COMPOUND_PREPOSITIONS = {('di', 'atas'): 'の上に', ('di', 'bawah'): 'の下に', ('di', 'dalam'): 'の中に',
                         ('di', 'luar'): 'の外に', ('di', 'depan'): 'の前に', ('di', 'belakang'): 'の後ろに',
                         ('di', 'samping'): 'の横に', ('di', 'sebelah'): 'の隣に', ('di', 'antara'): 'の間に',
                         ('ke', 'dalam'): 'の中へ', ('ke', 'luar'): 'の外へ', ('dari', 'dalam'): 'の中から',
                         ('ke', 'atas'): 'の上へ', ('dari', 'atas'): 'の上から', ('di', 'tengah'): 'の真ん中に'}

VOWELS = 'aeiou'


def _item(surface, **kw):
    item = {'surface': surface, 'compact': True}
    item.update(kw)
    return item


def _nominal_cngs(number='sg'):
    return [(case, number, GENDER) for case in CASES]


def _adj_cngs():
    return [(case, number, GENDER) for case in CASES for number in ('sg', 'pl')]


# ----------------------------------------------------------------------
# 接辞を外す

def _men_roots(rest):
    """meN- / peN- の後ろ (鼻音を含む) → 語根の候補"""
    out = []
    if rest.startswith('ny') and len(rest) > 2 and rest[2] in VOWELS:
        out.append('s' + rest[2:])                    # menyapu ← sapu
    if rest.startswith('ng'):
        tail = rest[2:]
        if tail[:1] in VOWELS:
            out += ['k' + tail, tail]                  # mengirim ← kirim、mengambil ← ambil
        elif tail[:1] in ('g', 'h', 'k'):
            out.append(tail)                           # menggambar ← gambar、menghitung ← hitung
        if tail.startswith('e'):
            out.append(tail[1:])                       # mengecat ← cat (1音節の語根)
    elif rest.startswith('m'):
        tail = rest[1:]
        if tail[:1] in VOWELS:
            out.append('p' + tail)                     # memakai ← pakai
        if tail[:1] in ('b', 'f', 'p', 'v'):
            out.append(tail)                           # membaca ← baca
        out.append(rest)                               # memasak? / mempunyai は下の memper-
    elif rest.startswith('n'):
        tail = rest[1:]
        if tail[:1] in VOWELS:
            out.append('t' + tail)                     # menulis ← tulis
        if tail[:1] in ('d', 'c', 'j', 'z', 's', 't'):
            out.append(tail)                           # mendengar ← dengar、mencari ← cari
        out.append(rest)
    else:
        out.append(rest)                               # melihat ← lihat、merasa ← rasa、menanti
    return out


SUFFIXES = (('kan', '-kan'), ('i', '-i'), ('an', '-an'), ('', ''))


@functools.lru_cache(maxsize=50000)
def derivations(word):
    """語 → [(語根, 接辞の説明, 種類)]。種類: active (meN-), passive (di-), ber, ter, noun_ke_an, noun_pe, …"""
    out = []

    def add(root, label, kind):
        if root and len(root) >= 2 and (root, label, kind) not in out:
            out.append((root, label, kind))

    for suffix, slabel in SUFFIXES:
        if suffix and not word.endswith(suffix):
            continue
        stem = word[:-len(suffix)] if suffix else word
        if len(stem) < 3:
            continue
        sl = (' + ' + slabel) if slabel else ''
        if stem.startswith('memper'):
            add(stem[6:], 'memper-' + sl, 'active')
        if stem.startswith('diper'):
            add(stem[5:], 'diper-' + sl, 'passive')
        if stem.startswith('me') and len(stem) > 4:
            for root in _men_roots(stem[2:]):
                add(root, 'meN-' + sl, 'active')
        if stem.startswith('di'):
            add(stem[2:], 'di-' + sl, 'passive')
        if stem.startswith(('ber', 'bel')):
            add(stem[3:], 'ber-' + sl, 'ber')
            add('r' + stem[3:], 'ber-' + sl, 'ber')        # berencana ← rencana (r が1つ落ちる)
        if stem.startswith('be') and stem[2:3] == 'r':
            pass
        elif stem.startswith('be'):
            add(stem[2:], 'ber-' + sl, 'ber')            # bekerja ← kerja
        if stem.startswith('ter'):
            add(stem[3:], 'ter-' + sl, 'ter')
            add('r' + stem[3:], 'ter-' + sl, 'ter')        # terasa ← rasa
        if suffix == 'an' and stem.startswith('ke'):
            add(stem[2:], 'ke-…-an', 'noun_ke_an')
        if suffix == 'an' and stem.startswith('per'):
            add(stem[3:], 'per-…-an', 'noun_per_an')
        if stem.startswith('pe') and len(stem) > 4:
            for root in _men_roots(stem[2:]):
                add(root, 'peN-' + sl, 'noun_pe_an' if suffix == 'an' else 'noun_pe')
        if stem.startswith('se') and not suffix:
            add(stem[2:], 'se-', 'se')
        if suffix and not any(stem.startswith(p) for p in ('me', 'di', 'ber', 'be', 'ter', 'ke', 'pe', 'per', 'se')):
            add(stem, slabel, 'suffix')
    return out


# ----------------------------------------------------------------------
# 項目

def _entries(key, lang):
    """辞書の項目 (つながりは引き当てる: membaca → active of baca → baca の訳語)"""
    rows = dictionary.lemmas(key, lang)
    out = []
    for row in rows:
        if not row['en'] and row['target']:
            for target in dictionary.lemmas(row['target'], lang):
                if target['en']:
                    out.append(dict(target, link=row['link'], linked_from=key, pos=row['pos'] or target['pos']))
                    break
            else:
                continue
        elif row['en'] or row['pos'] in ('preposition', 'conj', 'pronoun'):
            out.append(row)
    return out


def _gloss(key, pos):
    if key in GLOSSES and (GLOSSES[key][1] == pos or pos is None):
        return GLOSSES[key][0], 'ja'
    return None


def _make(surface, entry, base, kind=None, label=None):
    pos = entry['pos']
    fixed = _gloss(surface, pos) or _gloss(base, pos)  # 派生形そのものの訳語を先に (membangun → 建設する)
    ja, gloss_lang = fixed if fixed else (entry['en'], 'en')
    describe = base if not label else '%s (%s)' % (base, label)
    if pos == 'verb' or kind in ('active', 'passive'):
        voice = 'passive' if kind == 'passive' or entry.get('link') == 'passive' else 'active'
        return _item(surface, pos='verb', pres1sg=base, lemma=base, base=describe, ja=ja, gloss_lang=gloss_lang,
                     voice=voice, mood='indicative', tense='present', person=None, number=None, main=True,
                     derivation=label or entry.get('link') or '')
    if pos in ('adj',):
        return _item(surface, pos='adj', base=describe, ja=ja, gloss_lang=gloss_lang, lemma=base,
                     derivation=label or '', _=_adj_cngs())
    if pos == 'name':
        return _item(surface, pos='noun', base=describe, ja=surface[:1].upper() + surface[1:], gloss_lang='en',
                     proper=True, lemma=base, _=_nominal_cngs())
    if pos in ('noun', 'pronoun', 'num', 'classifier', 'det', 'root'):
        number = 'pl' if entry.get('link') == 'plural' else 'sg'
        return _item(surface, pos='noun' if pos != 'pronoun' else 'pronoun', base=describe, ja=ja,
                     gloss_lang=gloss_lang, lemma=base, derivation=label or '', _=_nominal_cngs(number))
    if pos == 'adv':
        return _item(surface, pos='adv', base=describe, ja=ja, gloss_lang=gloss_lang)
    return None


def _function_word(word):
    """機能語の項目 (前置詞・接続詞・代名詞・指示詞・相の副詞・否定・繋辞)"""
    if word in NAMES:
        return [_item(word, pos='noun', base=word, ja=NAMES[word], gloss_lang='ja', proper=True,
                      _=_nominal_cngs())]
    if word in DEMONSTRATIVES:
        attr, pron = DEMONSTRATIVES[word]
        return [_item(word, pos='adj', base=word, ja=attr, gloss_lang='ja', demonstrative=True, ja_pronoun=pron,
                      _=_adj_cngs())]
    if word in PRONOUNS:
        ja, person, number = PRONOUNS[word]
        return [_item(word, pos='pronoun', base=word, ja=ja, gloss_lang='ja', person=person, _=_nominal_cngs(number))]
    if word in PREPOSITIONS and PREPOSITIONS[word]:
        return [_item(word, pos='preposition', base=word, ja=PREPOSITIONS[word], gloss_lang='ja', dominates='Gen')]
    if word in CONJUNCTIONS and CONJUNCTIONS[word]:
        return [_item(word, pos='conj', base=word, ja=CONJUNCTIONS[word], gloss_lang='ja')]
    if word in ASPECTS:
        return [_item(word, pos='aspect', base=word, ja='', gloss_lang='ja', aspect=ASPECTS[word])]
    if word in NEGATIONS:
        return [_item(word, pos='adv', base=word, ja='〜ない', gloss_lang='ja', negation=True)]
    if word in COPULAS:
        return [_item(word, pos='verb', pres1sg='adalah' if word != 'menjadi' else 'menjadi', lemma=word, base=word,
                      ja=COPULAS[word], gloss_lang='ja', voice='active', mood='indicative', tense='present',
                      person=None, number=None, main=True, copula=word != 'menjadi')]
    if word in PRENOMINAL:
        return [_item(word, pos='adj', base=word, ja=PRENOMINAL[word], gloss_lang='ja', prenominal=True,
                      _=_adj_cngs())]
    if word in MODALS:
        return [_item(word, pos='modal', base=word, ja='', gloss_lang='ja', modal=MODALS[word])]
    if word in ADVERBS:
        return [_item(word, pos='adv', base=word, ja=ADVERBS[word], gloss_lang='ja')]
    if word == 'yang':
        return [_item(word, pos='relative', base=word, ja='', gloss_lang='ja')]
    return None


@functools.lru_cache(maxsize=50000)
def analyze(word, lang='id'):
    """語 (小文字) → [項目] (良いものから)。接語 (-nya, -ku, -mu, -lah, -kah, -pun) は別に返す: ([項目], 接語)"""
    function = _function_word(word)
    if function:
        return function, None
    for clitic in list(PARTICLE_CLITICS) + list(CLITICS):
        if word.endswith(clitic) and len(word) > len(clitic) + 2:
            host = word[:-len(clitic)]
            items, _ = analyze(host, lang)
            if items and not items[0].get('unknown') and not _entries(word, lang):
                return items, clitic
    entries = _entries(word, lang)
    items = []
    for entry in entries:
        item = _make(word, entry, entry.get('linked_from') and entry.get('word', word).lower() or word,
                     label={'active': 'meN-', 'passive': 'di-'}.get(entry.get('link')))
        if item and item['pos'] not in [i['pos'] for i in items]:
            items.append(item)
    if word in GLOSSES and not any(i['pos'] == GLOSSES[word][1] for i in items):
        items.insert(0, _make(word, {'pos': GLOSSES[word][1], 'en': ''}, word))
    if '-' in word:
        first, second = word.split('-', 1)
        if first == second or second.startswith(first[:3]):
            base, _ = analyze(first, lang)
            for item in base:
                if item['pos'] == 'noun':
                    plural = dict(item, surface=word, _=_nominal_cngs('pl'), base=item['base'] + ' (重複: 複数)')
                    items.insert(0, plural)
                    break
            if not items and base:
                items = [dict(base[0], surface=word)]
    if not items:
        for root, label, kind in derivations(word):
            root_entries = _entries(root, lang)
            if not root_entries and root not in GLOSSES:
                continue
            if root in GLOSSES and not root_entries:
                root_entries = [{'pos': GLOSSES[root][1], 'en': ''}]
            for entry in root_entries:
                if kind in ('active', 'passive') and entry['pos'] not in ('verb', 'noun', 'adj', 'root'):
                    continue
                if kind.startswith('noun'):
                    e = dict(entry, pos='noun')
                elif kind == 'ber':
                    e = dict(entry, pos='verb' if entry['pos'] != 'adj' else 'adj')
                elif kind == 'ter' and entry['pos'] == 'adj':
                    e = dict(entry, pos='adj', en='most ' + (entry['en'] or '').split(',')[0] if entry['en'] else '')
                else:
                    e = entry
                item = _make(word, e, root, kind, label)
                if item:
                    if kind == 'ter' and entry['pos'] == 'adj' and not _gloss(root, 'adj'):
                        item['superlative'] = True
                    if kind == 'ter' and entry['pos'] == 'adj' and _gloss(root, 'adj'):
                        item.update(ja='最も' + _gloss(root, 'adj')[0], gloss_lang='ja')
                    items.append(item)
                break
            if items:
                break
    if word.startswith('di') and items and not any(i['pos'] == 'verb' for i in items):
        # di- の語の形容詞の項目 (disebut「呼ばれた」) より、語根の動詞の受動を先に
        for root, label, kind in derivations(word):
            if kind == 'passive' and any(e['pos'] == 'verb' for e in _entries(root, lang)):
                entry = next(e for e in _entries(root, lang) if e['pos'] == 'verb')
                items.insert(0, _make(word, entry, root, kind, label))
                break
    if not items:
        if re.match('^(di|me[mn]?|ber|ter)[a-z]{3,}', word):
            # 辞書に無い di- / meN- / ber- / ter- の語は動詞 (解析の述語を見落とさないように)
            voice = 'passive' if word.startswith('di') else 'active'
            items = [_item(word, pos='verb', pres1sg=word, lemma=word, base=word, ja=word, gloss_lang='en',
                           voice=voice, mood='indicative', tense='present', person=None, number=None, main=True,
                           unknown=True)]
        else:
            items = [_item(word, pos='noun', base=word, ja=word, gloss_lang='en', unknown=True, _=_nominal_cngs())]
    return items, None
