#!/usr/bin/env python3
"""
Оптимизация index.html для iframe в Google Sites:
1. LCP: mobile-first 640w для первого picture
2. CSS: overflow-x, body margin/padding
3. decoding="async" на всех img кроме LCP
4. "Показать ещё" для мобильных (16 товаров)
"""

import re

def optimize_index_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # === 1. CSS: overflow-x, body margin/padding ===
    # Добавляем overflow-x:hidden к html
    html = html.replace(
        'html{scroll-behavior:smooth;font-size:16px}',
        'html{scroll-behavior:smooth;font-size:16px;overflow-x:hidden}'
    )
    # Добавляем margin:0;padding:0 к body
    html = html.replace(
        'body{font-family:var(--font-body);background-color:var(--color-bg);color:var(--color-text);line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased}',
        'body{font-family:var(--font-body);background-color:var(--color-bg);color:var(--color-text);line-height:1.6;overflow-x:hidden;margin:0;padding:0;-webkit-font-smoothing:antialiased}'
    )

    # === 2. LCP: первый picture (dress-01) — mobile-first 640w ===
    # Находим первый picture блок
    first_picture_pattern = r'(<picture class="product-picture">)(.*?)(</picture>)'
    
    def replace_first_picture(match):
        content = match.group(2)
        # Добавляем mobile-first source для avif
        new_content = content.replace(
            '<source type="image/avif" srcset="images/dress-01-160.avif 160w, images/dress-01-320.avif 320w, images/dress-01-640.avif 640w, images/dress-01-960.avif 960w, images/dress-01.avif 1024w" sizes="(max-width: 360px) 100vw, (max-width: 480px) 100vw, (max-width: 768px) 50vw, 260px">',
            '<!-- LCP: mobile-first 640w --><source type="image/avif" media="(max-width:480px)" srcset="images/dress-01-640.avif 640w" sizes="100vw"><source type="image/avif" srcset="images/dress-01-160.avif 160w, images/dress-01-320.avif 320w, images/dress-01-640.avif 640w, images/dress-01-960.avif 960w, images/dress-01.avif 1024w" sizes="(max-width:768px) 50vw, 260px">'
        )
        # Добавляем mobile-first source для webp
        new_content = new_content.replace(
            '<source type="image/webp" srcset="images/dress-01-160.webp 160w, images/dress-01-320.webp 320w, images/dress-01-640.webp 640w, images/dress-01-960.webp 960w, images/dress-01.webp 1024w" sizes="(max-width: 360px) 100vw, (max-width: 480px) 100vw, (max-width: 768px) 50vw, 260px">',
            '<source type="image/webp" media="(max-width:480px)" srcset="images/dress-01-640.webp 640w" sizes="100vw"><source type="image/webp" srcset="images/dress-01-160.webp 160w, images/dress-01-320.webp 320w, images/dress-01-640.webp 640w, images/dress-01-960.webp 960w, images/dress-01.webp 1024w" sizes="(max-width:768px) 50vw, 260px">'
        )
        return match.group(1) + new_content + match.group(3)
    
    html = re.sub(first_picture_pattern, replace_first_picture, html, count=1, flags=re.DOTALL)

    # === 3. decoding="async" на всех img кроме LCP ===
    # У первого img (LCP) убираем decoding="async" если есть
    # Находим первый <img после первого picture
    first_img_pattern = r'(<picture class="product-picture">.*?<img src="images/dress-01-640.jpg") decoding="async"'
    html = re.sub(first_img_pattern, r'\1', html, count=1, flags=re.DOTALL)
    
    # У всех остальных img добавляем decoding="async" если нет
    # Сначала заменяем loading="eager" на loading="lazy" + decoding="async" (кроме первого)
    # Но первый уже обработан, так что просто убедимся что у всех остальных есть decoding="async"
    img_count = 0
    def add_decoding_async(match):
        nonlocal img_count
        img_count += 1
        if img_count == 1:
            # Первое изображение (LCP) — без decoding="async"
            return match.group(0).replace(' decoding="async"', '')
        else:
            # Остальные — с decoding="async"
            if 'decoding="async"' not in match.group(0):
                return match.group(0).replace('<img', '<img decoding="async"')
            return match.group(0)
    
    # Проще: заменим все img через regex
    # Сначала убираем decoding="async" у первого img
    # Находим все img теги
    all_imgs = list(re.finditer(r'<img[^>]+>', html))
    
    for i, m in enumerate(all_imgs):
        old = m.group(0)
        if i == 0:
            # LCP: убираем decoding="async" если есть
            new = old.replace(' decoding="async"', '')
        else:
            # Остальные: добавляем decoding="async" если нет
            if 'decoding="async"' not in old:
                new = old.replace('<img ', '<img decoding="async" ')
            else:
                new = old
        html = html.replace(old, new, 1)

    # === 4. "Показать ещё" для мобильных ===
    # Находим closing </body> и добавляем скрипт перед ним
    show_more_script = '''
<script>(function(){var isMobile=window.innerWidth<768;if(isMobile){var sections=document.querySelectorAll('.product-grid');var totalShown=0;var maxInitial=16;var lastContainer=null;sections.forEach(function(grid){var items=grid.querySelectorAll('.product-card');items.forEach(function(card,index){if(totalShown>=maxInitial){card.style.display='none'}totalShown++});lastContainer=grid});if(lastContainer){var btn=document.createElement('button');btn.textContent='Показать ещё платья →';btn.className='show-more-btn';btn.onclick=function(){document.querySelectorAll('.product-card[style*="display: none"]').forEach(function(c){c.style.display=''});btn.style.display='none'};lastContainer.parentNode.appendChild(btn);var style=document.createElement('style');style.textContent='.show-more-btn{display:block;width:90%;max-width:400px;margin:30px auto;padding:16px 24px;background:#d4af37;color:#0a0a0a;border:none;border-radius:8px;font-size:1.1rem;font-weight:700;cursor:pointer;text-align:center;min-height:44px}';document.head.appendChild(style)}}})();</script>'''
    
    html = html.replace('</body>', show_more_script + '\n</body>')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] {filepath} optimized")
    return True

def optimize_landing_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # === 1. LCP: preload 640 вместо 320 ===
    html = html.replace(
        'href="images/dress-01-320.avif"',
        'href="images/dress-01-640.avif"'
    )

    # === 2. Первый picture — mobile-first 640w ===
    # Находим первый picture
    first_pic_pattern = r'(<picture>)(.*?)(</picture>)'
    
    def replace_landing_first_pic(match):
        content = match.group(2)
        # Добавляем mobile-first source для avif
        new_content = content.replace(
            '<source type="image/avif" srcset="images/dress-01-320.avif 320w, images/dress-01-640.avif 640w, images/dress-01-960.avif 960w, images/dress-01.avif 1024w" sizes="(max-width: 700px) 100vw, 50vw">',
            '<!-- LCP: mobile-first 640w --><source type="image/avif" media="(max-width:480px)" srcset="images/dress-01-640.avif 640w" sizes="100vw"><source type="image/avif" srcset="images/dress-01-320.avif 320w, images/dress-01-640.avif 640w, images/dress-01-960.avif 960w, images/dress-01.avif 1024w" sizes="(max-width:700px) 100vw, 50vw">'
        )
        new_content = new_content.replace(
            '<source type="image/webp" srcset="images/dress-01-320.webp 320w, images/dress-01-640.webp 640w, images/dress-01-960.webp 960w, images/dress-01.webp 1024w" sizes="(max-width: 700px) 100vw, 50vw">',
            '<source type="image/webp" media="(max-width:480px)" srcset="images/dress-01-640.webp 640w" sizes="100vw"><source type="image/webp" srcset="images/dress-01-320.webp 320w, images/dress-01-640.webp 640w, images/dress-01-960.webp 960w, images/dress-01.webp 1024w" sizes="(max-width:700px) 100vw, 50vw">'
        )
        # У первого img убираем decoding="async"
        new_content = new_content.replace(
            '<img src="images/dress-01-640.jpg"',
            '<img src="images/dress-01-640.jpg"'
        )
        return match.group(1) + new_content + match.group(3)
    
    html = re.sub(first_pic_pattern, replace_landing_first_pic, html, count=1, flags=re.DOTALL)

    # === 3. У первого img убираем decoding="async" ===
    html = html.replace(
        '<img src="images/dress-01-640.jpg" srcset="images/dress-01-320.jpg 320w, images/dress-01-640.jpg 640w, images/dress-01-960.jpg 960w, images/dress-01.jpg 1024w" sizes="(max-width: 700px) 100vw, 50vw" alt="Red Ballgown Prom Dress" loading="eager" decoding="async" fetchpriority="high">',
        '<img src="images/dress-01-640.jpg" srcset="images/dress-01-320.jpg 320w, images/dress-01-640.jpg 640w, images/dress-01-960.jpg 960w, images/dress-01.jpg 1024w" sizes="(max-width: 700px) 100vw, 50vw" alt="Red Ballgown Prom Dress" loading="eager" fetchpriority="high">'
    )

    # === 4. Critical CSS: body opacity ===
    html = html.replace(
        '<style>',
        '<style>body{opacity:0}body.loaded{opacity:1;transition:opacity .3s ease}'
    )

    # === 5. JS: add loaded class ===
    html = html.replace(
        '</script></body>',
        'document.body.classList.add("loaded")</script></body>'
    )
    # Находим closing script + body
    html = html.replace(
        'if(\'serviceWorker\'in navigator){window.addEventListener(\'load\',()=>{navigator.serviceWorker.register(\'/sw.js\')})}',
        'if(\'serviceWorker\'in navigator){window.addEventListener(\'load\',()=>{navigator.serviceWorker.register(\'/sw.js\')})};document.body.classList.add(\'loaded\')'
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] {filepath} optimized")
    return True

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'landing':
        optimize_landing_html('../landing.html')
    else:
        optimize_index_html('../index.html')
        optimize_landing_html('../landing.html')
