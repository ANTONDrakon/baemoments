#!/usr/bin/env python3
"""
HTML/CSS/JS Minifier for Bae Moments project.
Запуск: python scripts/minify.py

Минифицирует HTML, inline CSS и JS в index.html и landing.html.
Использует только встроенные возможности Python (без внешних зависимостей).
"""

import re
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES_TO_MINIFY = ['index.html', 'landing.html']


def minify_html(html: str) -> str:
    """Минифицирует HTML: удаляет лишние пробелы, комментарии, переносы строк."""
    # Удаляем HTML-комментарии (но сохраняем conditional comments для IE)
    html = re.sub(r'<!--(?!\[).*?-->', '', html, flags=re.DOTALL)
    
    # Удаляем лишние пробелы между тегами
    html = re.sub(r'>\s+<', '><', html)
    
    # Удаляем лишние пробелы в начале и конце строк
    html = re.sub(r'^\s+', '', html, flags=re.MULTILINE)
    html = re.sub(r'\s+$', '', html, flags=re.MULTILINE)
    
    # Удаляем множественные переносы строк
    html = re.sub(r'\n\s*\n', '\n', html)
    
    # Удаляем пробелы перед закрывающими тегами
    html = re.sub(r'\s+>', '>', html)
    
    # Удаляем пробелы после открывающих тегов
    html = re.sub(r'<\s+', '<', html)
    
    return html.strip()


def minify_css(css: str) -> str:
    """Минифицирует CSS: удаляет пробелы, комментарии, лишние точки с запятой."""
    # Удаляем комментарии
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    
    # Удаляем пробелы вокруг : ; , { }
    css = re.sub(r'\s*:\s*', ':', css)
    css = re.sub(r'\s*;\s*', ';', css)
    css = re.sub(r'\s*,\s*', ',', css)
    css = re.sub(r'\s*\{\s*', '{', css)
    css = re.sub(r'\s*\}\s*', '}', css)
    
    # Удаляем лишние пробелы
    css = re.sub(r'\s+', ' ', css)
    
    # Удаляем последнюю точку с запятой перед }
    css = re.sub(r';}', '}', css)
    
    # Удаляем пробелы в конце
    css = css.strip()
    
    return css


def minify_js(js: str) -> str:
    """Минифицирует JavaScript: удаляет комментарии, лишние пробелы, переносы строк."""
    # Удаляем однострочные комментарии
    js = re.sub(r'//[^\n]*', '', js)
    
    # Удаляем многострочные комментарии
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
    
    # Удаляем лишние пробелы и переносы строк
    js = re.sub(r'\s+', ' ', js)
    
    # Удаляем пробелы вокруг операторов где безопасно
    js = re.sub(r'\s*([=+\-*/%<>!&|?:;{},()\[\]])\s*', r'\1', js)
    
    # Удаляем лишние точки с запятой
    js = re.sub(r';+', ';', js)
    
    # Удаляем пробелы в начале и конце
    js = js.strip()
    
    return js


def minify_inline_styles(html: str) -> str:
    """Находит и минифицирует inline CSS в <style> тегах."""
    def _replace_style(match):
        css = match.group(1)
        minified = minify_css(css)
        return f'<style>{minified}</style>'
    
    return re.sub(r'<style>(.*?)</style>', _replace_style, html, flags=re.DOTALL)


def minify_inline_scripts(html: str) -> str:
    """Находит и минифицирует inline JS в <script> тегах (кроме JSON-LD)."""
    def _replace_script(match):
        script_type = match.group(1) or ''
        js = match.group(3)
        
        # Пропускаем JSON-LD и скрипты с type="application/ld+json"
        if 'ld+json' in script_type or 'json' in script_type:
            return match.group(0)
        
        # Пропускаем пустые скрипты (src атрибуты)
        if not js or not js.strip():
            return match.group(0)
        
        minified = minify_js(js)
        if script_type:
            return f'<script type="{script_type}">{minified}</script>'
        return f'<script>{minified}</script>'
    
    return re.sub(r'<script\s*(type="([^"]*)")?\s*>(.*?)</script>', _replace_script, html, flags=re.DOTALL)


def minify_file(filepath: str) -> None:
    """Минифицирует HTML файл."""
    print(f'  Processing: {filepath}')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content)
    
    # Минифицируем inline CSS
    content = minify_inline_styles(content)
    
    # Минифицируем inline JS
    content = minify_inline_scripts(content)
    
    # Минифицируем HTML
    content = minify_html(content)
    
    minified_size = len(content)
    savings = original_size - minified_size
    percent = (savings / original_size * 100) if original_size > 0 else 0
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'    Original: {original_size} bytes')
    print(f'    Minified: {minified_size} bytes')
    print(f'    Saved:    {savings} bytes ({percent:.1f}%)')


def main():
    print('=' * 50)
    print('  Bae Moments HTML/CSS/JS Minifier')
    print('=' * 50)
    print()
    
    for filename in FILES_TO_MINIFY:
        filepath = os.path.join(PROJECT_DIR, filename)
        if os.path.exists(filepath):
            minify_file(filepath)
        else:
            print(f'  SKIP: {filename} not found at {filepath}')
    
    print()
    print('  Done! All files minified.')


if __name__ == '__main__':
    main()
