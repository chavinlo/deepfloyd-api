from os.path import join, abspath, dirname
import traceback
import time
from io import BytesIO
import base64
from transformers import T5EncoderModel
from diffusers import DiffusionPipeline
import torch
from PIL import Image
import random

def image_generator(config, request_queue, image_queue):
    
    print("Starting engines...")

    gpu = config['gpu']
    device = f'cuda:{gpu}'

    print("Loading Text Encoder...")

    text_encoder = T5EncoderModel.from_pretrained(
        "DeepFloyd/IF-I-XL-v1.0",
        subfolder="text_encoder"
    )
    
    print("Loading Diffusion Pipeline Stage Text...")

    txt_pipe = DiffusionPipeline.from_pretrained(
        "DeepFloyd/IF-I-XL-v1.0", 
        text_encoder=text_encoder,
        unet=None
    )

    print("Loading Diffusion Pipeline Stage I...")

    i_pipe = DiffusionPipeline.from_pretrained(
        "DeepFloyd/IF-I-XL-v1.0", 
        text_encoder=None, 
        variant="fp16", 
        torch_dtype=torch.float16, 
    ).to(device)

    print("Loading Diffusion Pipeline Stage II...")

    ii_pipe = DiffusionPipeline.from_pretrained(
        "DeepFloyd/IF-II-L-v1.0", 
        text_encoder=None,
        variant="fp16", 
        torch_dtype=torch.float16
    ).to(device)

    print("Loading Diffusion Pipeline Stage III...")

    iii_pipe = DiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-x4-upscaler", 
        torch_dtype=torch.float16
    ).to(device)
    
    print("Loading Watermark...")

    water = Image.open("water.png")
    watermark = water.resize((96, 96))

    print("Engines ready!")

    def imgq(status: str, content):
        response = {
            "status": status,
            "content": content
        }
        image_queue.put(response)

    while True:
        print("Waiting for request...")
        request = request_queue.get()
        data = request
        print("Placed request:", data)
        try:
            start_time = time.time()

            prompt = data['prompt']
            negative_prompt = data['negative_prompt']
            steps = data['steps']

            # grab steps
            stage_1_steps = steps['stage_1']
            stage_2_steps = steps['stage_2']

            guidance = data['guidance']
            seed = data['seed']

            if seed == -1:
                seed = random.random()

            generator = torch.Generator().manual_seed(int(seed))

            prompt_embeds, negative_embeds = txt_pipe.encode_prompt(
                prompt=prompt,
                negative_prompt=negative_prompt)

            image = i_pipe(
                prompt_embeds=prompt_embeds,
                negative_prompt_embeds=negative_embeds, 
                output_type="pt",
                generator=generator,
                num_inference_steps=int(stage_1_steps),
                guidance_scale=float(guidance)
            ).images

            image = ii_pipe(
                image=image, 
                prompt_embeds=prompt_embeds, 
                negative_prompt_embeds=negative_embeds, 
                output_type="pt",
                generator=generator,
                num_inference_steps=int(stage_2_steps),
                guidance_scale=float(guidance)
            ).images

            pil_image = iii_pipe(prompt, generator=generator, image=image).images
            image = pil_image[0]
            width, height = image.size
            watermarked_image = Image.new('RGB', (width, height), (255, 255, 255))
            watermarked_image.paste(image, (0, 0))
            watermarked_image.paste(watermark, (width - 96, height - 96), watermark)
            
            serving_time = time.time()
            buffered = BytesIO()
            watermarked_image.save(buffered, format="PNG")
            imgq("done", {"image": base64.b64encode(buffered.getvalue()).decode('utf-8')})
        except Exception as e:
            traceback.print_exc()
            imgq('fail', f'general exception, got {str(e)}')
            continue

