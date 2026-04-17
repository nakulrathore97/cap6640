import os
import argparse
import torch
from diffusers import SanaSprintPipeline
from transformers import AutoProcessor, AutoModel, CLIPModel, CLIPProcessor
import glob
from tqdm import tqdm
import json
from PIL import Image

seed = 42

def get_pickscore(model, processor, images, prompt):
    with torch.no_grad():
        inputs = processor(
            text=[prompt], 
            images=images, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=77
        ).to("cuda")
        outputs = model(**inputs)
        scores = outputs.logits_per_image
        return scores.cpu().item()

def get_clipscore(model, processor, images, prompt):
    with torch.no_grad():
        inputs = processor(
            text=[prompt], 
            images=images, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=77
        ).to("cuda")
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image 
        return logits_per_image.cpu().item()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="sana", choices=["sana", "z-image-turbo", "sd3.5"], help="Generative model to use")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if args.model == "sana":
        print("Loading Sana pipeline...")
        pipeline = SanaSprintPipeline.from_pretrained(
            "Efficient-Large-Model/Sana_Sprint_0.6B_1024px_diffusers",
            torch_dtype=torch.bfloat16,
        ).to(device)
    elif args.model == "z-image-turbo":
        print("Loading Z-Image-Turbo pipeline...")
        from diffusers import ZImagePipeline
        pipeline = ZImagePipeline.from_pretrained(
            "Tongyi-MAI/Z-Image-Turbo",
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=False,
        ).to(device)
    elif args.model == "sd3.5":
        print("Loading SD 3.5 Large Turbo pipeline...")
        from diffusers import StableDiffusion3Pipeline
        pipeline = StableDiffusion3Pipeline.from_pretrained(
            "stabilityai/stable-diffusion-3.5-large-turbo",
            torch_dtype=torch.bfloat16,
        ).to(device)
    
    print("Loading PickScore model...")
    processor_pick = AutoProcessor.from_pretrained("yuvalkirstain/PickScore_v1")
    model_pick = AutoModel.from_pretrained("yuvalkirstain/PickScore_v1").eval().to(device)

    print("Loading CLIP score model...")
    processor_clip = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")
    model_clip = CLIPModel.from_pretrained("openai/clip-vit-base-patch16").eval().to(device)
    
    txt_dir = "./txt_files_2"
    output_dir = f"./output_{args.model}"
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    txt_files = sorted(glob.glob(os.path.join(txt_dir, "*.txt")))
    file_pbar = tqdm(txt_files, desc="Files processed", position=0)
    total_prompts_generated = 0
    
    for txt_file in file_pbar:
        file_name = os.path.basename(txt_file)
        
        with open(txt_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
            
        file_pickscores = []
        file_clipscores = []
        
        file_out_dir = os.path.join(output_dir, file_name.replace(".txt", ""))
        os.makedirs(file_out_dir, exist_ok=True)
        
        prompt_pbar = tqdm(prompts, desc=file_name, position=1, leave=False)
        for i, prompt in enumerate(prompt_pbar):
            # Generate image
            if args.model == "sana":
                out = pipeline(
                    prompt=prompt,
                    height=1024,
                    width=1024,
                    num_inference_steps=2,
                    output_type="pil",
                    generator=torch.Generator(device=device).manual_seed(seed)
                )
            elif args.model == "z-image-turbo":
                out = pipeline(
                    prompt=prompt,
                    height=1024,
                    width=1024,
                    num_inference_steps=9,
                    guidance_scale=0.0,
                    output_type="pil",
                    generator=torch.Generator(device=device).manual_seed(seed)
                )
            elif args.model == "sd3.5":
                out = pipeline(
                    prompt=prompt,
                    height=1024,
                    width=1024,
                    num_inference_steps=4,
                    guidance_scale=0.0,
                    output_type="pil",
                    generator=torch.Generator(device=device).manual_seed(seed)
                )
            image = out.images[0]
            
            # Save image
            img_path = os.path.join(file_out_dir, f"{i:04d}.png")
            image.save(img_path)
            
            # Compute PickScore
            ps = get_pickscore(model_pick, processor_pick, [image], prompt)
            file_pickscores.append(ps)
            
            # Compute ClipScore
            cs = get_clipscore(model_clip, processor_clip, [image], prompt)
            file_clipscores.append(cs)
            
            total_prompts_generated += 1
            file_pbar.set_postfix(prompts_generated=total_prompts_generated)
            
        
        avg_pick = sum(file_pickscores) / len(file_pickscores) if file_pickscores else 0
        avg_clip = sum(file_clipscores) / len(file_clipscores) if file_clipscores else 0
        
        results[file_name] = {
            "avg_pickscore": avg_pick,
            "avg_clipscore": avg_clip,
            "num_prompts": len(prompts)
        }
        
        tqdm.write(f"File: {file_name} - Avg PickScore: {avg_pick:.4f}, Avg ClipScore: {avg_clip:.4f}")
        
        # Save progress after each folder
        with open(os.path.join(output_dir, "summary.json"), "w") as f:
            json.dump(results, f, indent=4)
            
        with open(os.path.join(file_out_dir, "results.json"), "w") as f:
            json.dump({
                "avg_pickscore": avg_pick,
                "avg_clipscore": avg_clip,
                "num_prompts": len(prompts),
                "pickscores": file_pickscores,
                "clipscores": file_clipscores
            }, f, indent=4)
        
    print("\nDone! Results summary saved in", os.path.join(output_dir, "summary.json"))

if __name__ == "__main__":
    main()
