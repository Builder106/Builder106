import asyncio
import os
from PIL import Image
from playwright.async_api import async_playwright
from io import BytesIO

async def create_flawless_apng():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 256, 'height': 256})
        
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
                    margin: 0; padding: 0; width: 256px; height: 256px; 
                    overflow: hidden; background-color: #0D1117; 
                }}
                svg {{ display: block; width: 256px; height: 256px; }}
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

        print("Capturing strictly opaque frames...")
        for i in range(total_frames):
            current_time = (i / fps) * 1000
            await page.evaluate(f"document.getAnimations().forEach(a => a.currentTime = {current_time})")
            
            screenshot_bytes = await page.screenshot()
            # THE FIX: Converting to RGB removes all transparency, forcing a solid square
            frames.append(Image.open(BytesIO(screenshot_bytes)).convert("RGB"))

        print("Shifting frames for Discord fallback...")
        shift_index = int(total_frames * 0.75)
        shifted_frames = frames[shift_index:] + frames[:shift_index]
        
        output_file = os.path.join(script_dir, "discord-perfect.png")
        print("Encoding solid Animated PNG...")
        
        # Removed disposal=2. Opaque frames drawn over opaque frames don't need disposal.
        shifted_frames[0].save(
            output_file,
            save_all=True,
            append_images=shifted_frames[1:],
            duration=33,
            loop=0
        )
        
        print(f"Success! {output_file} is a solid 256x256 block. No clipping possible.")
        await browser.close()

asyncio.run(create_flawless_apng())