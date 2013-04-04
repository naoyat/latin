.SUFFIXES:
.SUFFIXES: .src .txt

TRANS_SED = ../../scripts/trans.sed

.src.txt:
	sed -f $(TRANS_SED) $< > $@

TEXTS = \
	1.TESSEUS_ET_ARIADNE.txt \
	2.BELLUM_TROJANUM.txt \
	3.OMNIA_MUTANTUR.txt \
	4.CERES_ET_PERSEPHONE_1.txt \
	5.CERES_ET_PERSEPHONE_2.txt \
	6.CERES_ET_PERSEPHONE_3.txt \
	7.CERES_ET_PERSEPHONE_4.txt \
	8.CERES_ET_PERSEPHONE_5.txt \
	GLORIA.txt

all: $(TEXTS)

install: all
	mv $(TEXTS) ..

clean:
	rm -f *.txt *~
