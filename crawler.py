import os
import json
import asyncio
import aiohttp
from tqdm import tqdm
from bs4 import BeautifulSoup
import requests

# 从网页中获取表情图像链接
def get_emoji_urls():
    page = requests.get("https://9to5google.com/2021/09/24/gboard-emoji-kitchen-list/")
    soup = BeautifulSoup(page.content, "html.parser")
    imgs = soup.find_all("img")
    img_urls = [img["src"] for img in imgs]
    emoji_img_urls = [link for link in img_urls if link.find("production-standard-emoji-assets") != -1]
    emojis = [link.split("/")[-1][:-4] for link in emoji_img_urls]
    emojis = [emoji for emoji in emojis if len(emoji) == 5]
    return emojis

# 使用异步请求获取 URL 响应
async def fetch(session, url):
    async with session.head(url) as rep:
        return rep

# 并发请求获取表情图像链接
async def fetch_emoji_pairs(emoji_a, emojis, pattern20, emoji_pair_url):
    urls = [pattern20.format(x=emoji_a, y=emoji_b) for emoji_b in emojis]
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        reps = await asyncio.gather(*tasks)
        for i, rep in enumerate(reps):
            if rep is not None and rep.status == 200:
                emoji_b = emojis[i]
                emoji_pair_url[emoji_a][emoji_b] = urls[i]

# 从文件加载已保存的 URL 数据
def load_saved_urls():
    emoji_pair_url = {}
    if os.path.exists("emoji_urls.json"):
        with open("emoji_urls.json", "r") as f:
            emoji_pair_url = json.load(f)
    return emoji_pair_url

# 保存 URL 数据到文件
def save_urls_to_file(emoji_pair_url):
    with open("emoji_urls.json", "w") as f:
        json.dump(emoji_pair_url, f)

# 主函数
def main():
    emojis = get_emoji_urls()
    pattern20 = "https://www.gstatic.com/android/keyboard/emojikitchen/20201001/u{x}/u{x}_u{y}.png"
    emoji_pair_url = load_saved_urls()

    for emoji_a in tqdm(emojis):
        if emoji_a not in emoji_pair_url:
            emoji_pair_url[emoji_a] = {}
        asyncio.run(fetch_emoji_pairs(emoji_a, emojis, pattern20, emoji_pair_url))

    save_urls_to_file(emoji_pair_url)

    # 打印已保存的表情链接
    for emoji, urls in emoji_pair_url.items():
        print(f"{emoji}: {len(urls)} pairs")

if __name__ == "__main__":
    main()
