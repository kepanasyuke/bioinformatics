cwlVersion: v1.2
class: Workflow

label: Germline WGS, синтетический референс
doc: |
  Пять шагов от сырых fastq до отфильтрованного VCF.
  Каждый шаг запускается в своём контейнере с зафиксированной версией.

inputs:
  reads_r1: File
  reads_r2: File
  reference: File
  sample: string
  threads: int

outputs:
  filtered_vcf:
    type: File
    outputSource: filter/filtered
  qc_json:
    type: File
    outputSource: trim/report

steps:
  trim:
    run: steps/fastp.cwl
    in:
      r1: reads_r1
      r2: reads_r2
      sample: sample
      threads: threads
    out: [trimmed_r1, trimmed_r2, report]

  align:
    run: steps/bwa_mem2.cwl
    in:
      r1: trim/trimmed_r1
      r2: trim/trimmed_r2
      reference: reference
      sample: sample
      threads: threads
    out: [sorted_bam]

  markdup:
    run: steps/markdup.cwl
    in:
      bam: align/sorted_bam
      sample: sample
    out: [dedup_bam, metrics]

  call:
    run: steps/haplotypecaller.cwl
    in:
      bam: markdup/dedup_bam
      reference: reference
      sample: sample
      threads: threads
    out: [raw_vcf]

  filter:
    run: steps/bcftools_filter.cwl
    in:
      vcf: call/raw_vcf
      expression: default_filter
    out: [filtered]

requirements:
  ResourceRequirement:
    ramMin: 16000
    coresMin: 8
  InlineJavascriptRequirement: {}
