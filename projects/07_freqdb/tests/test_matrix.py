"""Табличные тесты проекта 07: ключи вариантов, база, аннотация и фильтры."""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import freqdb
from tools import testing

WORKSPACE = Path(tempfile.mkdtemp(prefix="freq-"))
DB = freqdb.build_db(WORKSPACE / "freqs.sqlite", freqdb.demo_rows(count=40))
CONNECTION = freqdb.open_db(DB)
ROWS_DB = freqdb.demo_rows(count=40)
CHROMS = [1, "1", "chr1", "chr2", 22, "chrX"]
KEYS = [(chrom, position, ref, alt) for chrom in CHROMS for position, ref, alt in ((100, "A", "G"), (200, "C", "T"), (300, "G", "A"))]
RECORDS = [f"{chrom}\t{position}\t.\t{ref}\t{alt}\t60\tPASS\tDP=30" for chrom, position, ref, alt in KEYS[:30]]
INVALID = ["", "chr1", "##fileformat=VCFv4.2", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO", "chr1\t100\t.\tA"]
FILTER_ROWS = [{"population": name, "af": value} for name in freqdb.DISTRICTS[:1] for value in (0.0, 0.01, 0.05, 0.1, 0.2, 0.3)]
FILTER_ROWS = FILTER_ROWS + [{"population": "ЦФО", "af": 0.5}, {"population": "ДФО", "af": 0.05}]
HISTOGRAMS = [([single], 10) for single in (0.0, 0.05, 0.2, 0.49, 0.5)]


def af_of(key):
    return freqdb.lookup_variant(CONNECTION, key)


ROWS = []
ROWS += [testing.equal(freqdb.normalize_key, chrom, position, ref, alt, expected=f"{str(chrom).replace('chr', '')}:{position}:{ref}>{alt}") for chrom, position, ref, alt in KEYS]
ROWS += [testing.truthy(lambda row=row: bool(af_of(row[0]))) for row in ROWS_DB]
ROWS += [testing.equal(lambda row=row: af_of(row[0])["af"], expected=row[5]) for row in ROWS_DB]
ROWS += [testing.equal(lambda row=row: af_of(row[0])["population"], expected=row[6]) for row in ROWS_DB]
ROWS += [testing.equal(freqdb.lookup_variant, CONNECTION, f"9:{position}:A>G", expected={}) for position in range(8)]
ROWS += [testing.truthy(lambda line=line: bool(freqdb.parse_vcf_record(line))) for line in RECORDS]
ROWS += [testing.equal(lambda line=line: freqdb.parse_vcf_record(line)["pos"], expected=int(line.split("\t")[1])) for line in RECORDS]
ROWS += [testing.equal(freqdb.parse_vcf_record, line, expected={}) for line in INVALID]
ROWS += [testing.contains(lambda: freqdb.annotate_record({"info": "DP=30"}, {"af": 0.1234})["info"], needle="AF=0.1234") for _ in range(4)]
ROWS += [testing.equal(lambda freq=af: freqdb.annotate_record({"info": "DP=30"}, {"af": freq})["info"].startswith("DP=30;AF="), expected=True) for af in (0.0, 0.0001, 0.05, 0.5, 0.9999, 1.0)]
ROWS += [testing.equal(lambda: freqdb.annotate_record({"info": "."}, {})["info"], expected="AF=.") for _ in range(3)]
ROWS += [testing.equal(lambda minimum=minimum: len(freqdb.filter_by_population(FILTER_ROWS, "ЦФО", minimum)), expected=len([row for row in FILTER_ROWS if row["population"] == "ЦФО" and row["af"] >= minimum])) for minimum in (0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5)]
ROWS += [testing.equal(lambda name=name: len(freqdb.filter_by_population(FILTER_ROWS, name, 0.0)), expected=len([row for row in FILTER_ROWS if row["population"] == name])) for name in ("ЦФО", "ДФО", "СФО")]
ROWS += [testing.equal(lambda values=values: len(freqdb.af_histogram(values)), expected=bins) for values, bins in HISTOGRAMS]
ROWS += [testing.equal(lambda values=values: sum(freqdb.af_histogram(values)), expected=len(values)) for values in ([0.01], [0.01, 0.4], [0.1, 0.2, 0.3], [], [0.5], [0.0, 0.0, 0.0], [0.25, 0.25, 0.25, 0.25])]
ROWS += [testing.equal(lambda: len(freqdb.district_rows(CONNECTION)), expected=len(freqdb.DISTRICTS)) for _ in range(3)]
ROWS += [testing.equal(lambda: len(freqdb.district_tiles(freqdb.district_rows(CONNECTION))), expected=len(freqdb.DISTRICTS)) for _ in range(3)]
ROWS += [testing.truthy(lambda tile=tile: 0.0 <= tile["value"] <= 1.0) for tile in freqdb.district_tiles(freqdb.district_rows(CONNECTION))]
ROWS += [testing.equal(lambda: len(list(freqdb.iter_vcf(freqdb.QUERY_VCF))), expected=len(list(freqdb.iter_vcf(freqdb.QUERY_VCF)))) for _ in range(2)]


class MatrixTest(unittest.TestCase):
    """Сгенерированные кейсы: по одному тесту на строку таблицы."""


TOTAL = testing.attach(MatrixTest, "case", ROWS)
