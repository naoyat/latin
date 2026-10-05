.SUFFIXES:
.SUFFIXES: .src .txt

TRANS_SED = ../../scripts/trans.sed

.src.txt:
	sed -f $(TRANS_SED) $< > $@

# 権利関係が不明なテキスト (教科書からの引用) は $LATIN_DATA/private-texts/src/ に置く
TEXTS = \
	GLORIA.txt \
	RIMINI.txt

all: $(TEXTS)

install: all
	mv $(TEXTS) ..

clean:
	rm -f *.txt *~
