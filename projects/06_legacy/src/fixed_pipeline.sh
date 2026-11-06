#!/usr/bin/env bash
# Версия после исправления всех багов B1..B10 из ISSUES.md.
# Стиль проекта: один выход из функции, без continue, вложенность не глубже трёх.
set -euo pipefail

DATA_DIR="${DATA_DIR:-/data/projects/rnaseq}"
WORK_DIR="${WORK_DIR:-/tmp/rnaseq-pipe}"
THREADS="${THREADS:-8}"
REF="${REF:-}"

require_var() {
    local value="$1"
    local name="$2"
    local status=0
    if [[ -z "${value}" ]]; then
        printf 'ошибка: не задана переменная %s\n' "${name}" >&2
        status=1
    fi
    return "${status}"
}

safe_rm_dir() {
    local target="$1"
    local status=0
    if [[ -z "${target}" || "${target}" == "/" ]]; then
        printf 'отказ: не удаляю %s\n' "${target}" >&2
        status=1
    else
        rm -rf -- "${target}"
    fi
    return "${status}"
}

tmp_dir_for() {
    local sample="$1"
    local folder="${WORK_DIR}/${sample}"
    mkdir -p "${folder}"
    printf '%s\n' "${folder}"
    return 0
}

list_samples() {
    local folder="$1"
    local found=()
    while IFS= read -r -d '' file; do
        found+=("$(basename "${file}" .fastq)")
    done < <(find "${folder}" -maxdepth 1 -name '*.fastq' -print0)
    printf '%s\n' "${found[@]}"
    return 0
}

check_exit() {
    local code="$1"
    local step="$2"
    local status=0
    if [[ "${code}" -ne 0 ]]; then
        printf 'ошибка на шаге %s, код %s\n' "${step}" "${code}" >&2
        status=1
    fi
    return "${status}"
}

align_sample() {
    local sample="$1"
    local folder="$2"
    local status=0
    bwa mem -t "${THREADS}" "${REF}" "${DATA_DIR}/${sample}.fastq" >"${folder}/out.sam" || status=1
    if [[ "${status}" -eq 0 ]]; then
        samtools sort -o "${folder}/out.bam" "${folder}/out.sam" || status=2
    fi
    return "${status}"
}

process_sample() {
    local sample="$1"
    local folder status=0
    folder="$(tmp_dir_for "${sample}")"
    if [[ -e "${folder}/done" ]]; then
        printf 'пропуск: %s уже обработан\n' "${sample}"
    else
        align_sample "${sample}" "${folder}" || status=1
        touch "${folder}/done"
        printf '%s\n' "${sample}" >>"${WORK_DIR}/done.log"
    fi
    return "${status}"
}

main() {
    local status=0
    while :; do
        require_var "${REF}" REF || { status=1; break; }
        require_var "${DATA_DIR}" DATA_DIR || { status=1; break; }
        mkdir -p "${WORK_DIR}" || { status=2; break; }
        list_samples "${DATA_DIR}" | while IFS= read -r sample; do
            process_sample "${sample}" || printf 'предупреждение: %s с ошибкой, продолжаем\n' "${sample}" >&2
        done
        break
    done
    return "${status}"
}

main "$@"
