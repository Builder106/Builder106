import asyncio
import os
from PIL import Image
from playwright.async_api import async_playwright
from io import BytesIO


async def create_apng(size: int, output_name: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': size, 'height': size})

        script_dir = os.path.dirname(os.path.abspath(__file__))
        svg_path = os.path.join(script_dir, 'quant-final.svg')
        with open(svg_path, 'r') as f:
            svg_content = f.read()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body, html {{
                    margin: 0; padding: 0; width: {size}px; height: {size}px;
                    overflow: hidden; background-color: #0D1117;
                }}
                svg {{ display: block; width: {size}px; height: {size}px; }}
            </style>
        </head>
        <body>
            {svg_content}
        </body>
        </html>
        """

        await page.set_content(html_content)

        frames = []
        fps = 30
        duration_sec = 4
        total_frames = fps * duration_sec

        print(f"Capturing {size}x{size} frames...")
        for i in range(total_frames):
            current_time = (i / fps) * 1000
            await page.evaluate(f"document.getAnimations().forEach(a => a.currentTime = {current_time})")

            screenshot_bytes = await page.screenshot()
            frames.append(Image.open(BytesIO(screenshot_bytes)).convert("RGB"))

        print("Shifting frames for Discord fallback...")
        shift_index = int(total_frames * 0.75)
        shifted_frames = frames[shift_index:] + frames[:shift_index]

        output_file = os.path.join(script_dir, output_name)
        print(f"Encoding {size}x{size} Animated PNG...")

        shifted_frames[0].save(
            output_file,
            save_all=True,
            append_images=shifted_frames[1:],
            duration=33,
            loop=0
        )

        print(f"Success! {output_file} is a solid {size}x{size} block. No clipping possible.")
        await browser.close()


async def main():
    # 256x256 for Discord avatar (500KB limit)
    await create_apng(256, "discord-perfect.png")

    # 500x500 for high-res use
    await create_apng(500, "discord-perfect-500x500.png")


asyncio.run(main())