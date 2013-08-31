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
	9.CERES_ET_PERSEPHONE_6.txt \
	10.CORIOLANUS.txt \
	11.ROMULUS_ET_SABINAE_1.txt \
	12.ROMULUS_ET_SABINAE_2.txt \
	13.EPISTULA.txt \
	14.ROMULUS_ET_MARS_1.txt \
	GLORIA.txt \
	RIMINI.txt

all: $(TEXTS)

install: all
	mv $(TEXTS) ..

clean:
	rm -f *.txt *~
