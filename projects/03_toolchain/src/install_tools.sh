#!/usr/bin/env bash
# Установка биоинформатических инструментов из манифеста.
# Стиль проекта: один выход из функции, без continue, вложенность не глубже трёх.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${SCRIPT_DIR}/../data/manifest.tsv"
CACHE="${SCRIPT_DIR}/../data/cache"
PREFIX="${PREFIX:-/opt/bio}"
DRY_RUN="${DRY_RUN:-1}"

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

have_tool() {
    local name="$1"
    local status=1
    if command -v "${name}" >/dev/null 2>&1; then
        status=0
    fi
    return "${status}"
}

fetch_source() {
    local url="$1"
    local dest="$2"
    local status=0
    if [[ -f "${dest}" ]]; then
        printf 'из кэша: %s\n' "${dest}"
    else
        mkdir -p "$(dirname "${dest}")"
        curl -fsSL "${url}" -o "${dest}" || status=1
    fi
    return "${status}"
}

check_sum() {
    local file="$1"
    local expected="$2"
    local actual=""
    local status=0
    actual="$(sha256sum "${file}" | awk '{print $1}')"
    if [[ "${actual}" != "${expected}" ]]; then
        printf 'ошибка: sha256 не совпал для %s\n' "${file}" >&2
        status=1
    fi
    return "${status}"
}

build_tool() {
    local name="$1"
    local version="$2"
    local status=0
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        printf '[dry-run] %s %s: ./configure --prefix=%s && make -j8 && make install\n' "${name}" "${version}" "${PREFIX}"
    else
        make -C "${name}-${version}" -j 8 install PREFIX="${PREFIX}" || status=1
    fi
    return "${status}"
}

install_jar() {
    local name="$1"
    local version="$2"
    local status=0
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        printf '[dry-run] %s %s: копирование jar и обёртка в %s/bin\n' "${name}" "${version}" "${PREFIX}"
    else
        mkdir -p "${PREFIX}/share/java" "${PREFIX}/bin"
        cp "${CACHE}/${name}-${version}.jar" "${PREFIX}/share/java/" || status=1
    fi
    return "${status}"
}

write_log() {
    local name="$1"
    local status="$2"
    local log="${CACHE}/install.log"
    mkdir -p "${CACHE}"
    printf '%s\t%s\t%s\n' "$(date -Iseconds)" "${name}" "${status}" >>"${log}"
    return 0
}

main() {
    local status=0
    while :; do
        require_var "${PREFIX}" PREFIX || { status=1; break; }
        if [[ ! -f "${MANIFEST}" ]]; then
            printf 'ошибка: нет манифеста %s\n' "${MANIFEST}" >&2
            status=1
            break
        fi
        have_tool java || printf 'предупреждение: java не найден в PATH\n'
        build_tool htslib 1.20 || { status=2; break; }
        write_log htslib "${status}"
        install_jar gatk 4.6.0.0 || { status=3; break; }
        write_log gatk "${status}"
        break
    done
    return "${status}"
}

main "$@"
