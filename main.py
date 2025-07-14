#!/usr/bin/env python3
import os
from glob import glob
from pathlib import Path

import re

MAIN_PATTERN = re.compile(
    r'''
    (?:\bdef\s+main\s*\(\s*                # Scala: def main(
       args\s*:\s*Array\s*

\[\s*String\s*\]

 #   args: Array[String]
       .+?\))                              
  | (?:\b(public\s+)?(static\s+)?void\s+  # Java: [public] [static] void main(
       main\s*\(\s*String\s*

\[\s*\]

\s*\w+ #   main(String[] args
       .+?\))                             
  | (?:\bobject\s+\w+\s+extends\s+App\b)  # Scala: object Foo extends App
    ''',
    re.IGNORECASE | re.VERBOSE
)

IMPORT_PATTERN = re.compile(r'^\s*import\s+([\w\.]+(?:\.\*)?)')

def find_main_funcs(files):
    found = []
    for scala_file in files:
        try:
            with open(scala_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if MAIN_PATTERN.search(line):
                        found.append(scala_file)
                        break
        except Exception as e:
            print(f'Error leyendo {scala_file}: {e}')
    return found

# Patrón para capturar imports

def extraer_imports_con_prefijo(scala_path: Path, prefix: str) -> list:
    """
    Lee un fichero .scala y devuelve solo los imports que comienzan con el prefijo dado.
    
    :param scala_path: Ruta al fichero .scala
    :param prefix: Prefijo del paquete a filtrar (e.g. 'com.scala.app')
    :return: Lista de imports que empiezan por prefix
    """
    resultados = []
    with open(scala_path, 'r', encoding='utf-8', errors='ignore') as f:
        for linea in f:
            match = IMPORT_PATTERN.match(linea)
            if match:
                imp = match.group(1)
                if imp.startswith(prefix):
                    resultados.append(imp)
    return resultados

import os
import re

def get_project_package(project_path, file_path):
    # 1) Compute package from file path
    dir_rel = (
        file_path
        .replace(project_path, '')
        .replace(os.sep + 'src' + os.sep, os.sep)
        .replace(os.sep + 'main' + os.sep, os.sep)
        .replace(os.sep + 'scala' + os.sep, os.sep)
        .strip(os.sep)
    )
    dir_divided = os.path.dirname(dir_rel).split(os.sep)
    pack = ".".join(dir_divided)

    imports = []
    if not pack:
        return imports

    # 2) Precompile regexes
    # matches 'import some.pkg.{A,B,C}'
    brace_re = re.compile(r'''
        ^import \s+           # import keyword
        (?P<pkg>[\w\.]+)      # package prefix, e.g. some.pkg
        \.\{                   # literal .{
        (?P<elems>[^}]+)       # everything up to closing }
        \}                     # closing brace
        ''', re.VERBOSE)

    # matches simple 'import some.pkg.Foo'
    simple_re = re.compile(r'^import\s+(?P<pkg>[\w\.]+)')

    # 3) Scan lines
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for raw in f:
            line = raw.strip()
            # only care about imports that mention our package
            if not line.startswith('import') or pack not in line:
                continue

            # 3a) curly‐brace expansion
            m = brace_re.match(line)
            if m:
                base = m.group('pkg')                # e.g. com.paquete.funcion
                elems = m.group('elems').split(',')  # ['CosaA', 'CosaB', 'CosaC']
                for e in elems:
                    imports.append(f"{base}.{e.strip()}")
                continue

            # 3b) simple import
            m2 = simple_re.match(line)
            if m2:
                imports.append(m2.group('pkg'))

    return imports

if __name__ == "__main__":
    project_root = "/Users/manuel/desarrollo/scala-examples"
    project_paths = []
    for fname in os.listdir(project_root):
        if os.path.isdir(os.path.join(project_root, fname)):
            project_paths.append(os.path.join(project_root,fname))

    for proj in project_paths:
        scala_files = [y for x in os.walk(proj) for y in glob(os.path.join(x[0], '*.scala'))]

        main_files = find_main_funcs(scala_files)
        for f in scala_files:
            print(str(f) + " " + str(get_project_package(proj, f)))
