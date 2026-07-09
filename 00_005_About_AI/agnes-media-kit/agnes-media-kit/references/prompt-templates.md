# Prompt 模板参考

## 文生图 (Text-to-Image)

### 风格前缀

将风格词放在 prompt 开头以获得最佳效果：

```
Modern anime art style, a girl with long blue hair...

Photorealistic, a cat on minimalist white background...

Pixel art style, 8-bit, retro game character...

Watercolor painting, a garden with blooming roses...

Stained glass design, a majestic phoenix...

Crayon drawing style, child's drawing of a house with rainbow...

Line art, black and white, intricate mandala pattern...
```

### 图生图 (Image-to-Image) 风格

描述**转换效果**而非重新描述图片内容：

```
Transform into oil painting, rich brush strokes, impasto texture...

Apply Ghibli style, soft pastel colors, warm lighting...

Turn into charcoal sketch, rough outlines, dark shadows...

Add neon cyberpunk overlays, glowing edges, rain reflections...
```

### 长 Prompt 模板

建议 ≥30 字符，以下模板可直接使用：

**物品摄影**:
```
A [物品] on a [color] [材质] background, studio lighting,
professional product photography, [lighting_type] lighting,
high detail, sharp focus, centered composition
```

**角色设计**:
```
A [style] character design of a [description], full body,
[pose], wearing [clothing], [color scheme] palette,
clean lines, expressive, character concept art
```

**场景描述**:
```
A [time_of_day] view of [location], [weather] atmosphere,
[style], [mood] lighting, [camera_type] lens,
breathtaking landscape, ultra detail, cinematic composition
```

---

## 文生视频 (Text-to-Video)

### 视频 Prompt 结构

```
[主语] + [动作/行为] + [环境/背景] + [气氛/风格] + [镜头语言]
```

**示例**:
```
A majestic lion walking slowly through golden savanna grass at sunset,
cinematic quality, slow motion, 4k, warm golden light, depth of field
```

```
Flowing digital particles of light forming a human silhouette,
dark background, blue and purple color scheme, sci-fi style,
smooth transition, hypnotic movement
```

### Ti2Vid (图生视频) Prompt

```
The [subject in image] starts [action], [environment details],
[camera movement], smooth motion, consistent character
```

**示例**:
```
The cat starts skateboarding down a gentle hill, wearing tiny sunglasses,
wheels spinning, wind blowing fur back, bright sunny day, cinematic quality
```

### 关键帧动画 Prompt

```
Smooth morphing transition between [frame1] and [frame2],
consistent style and subject, organic flow, seamless
```

---

## 中文 Prompt 支持

Agnes API 支持中文 prompt，但英文通常效果更精确。

**中文示例 — 文生图**:
```
一只银渐层猫在白色背景上，专业产品摄影，柔光照明，高清细节
```

**中文示例 — 文生视频**:
```
一只橘猫在沙滩上追逐蝴蝶，日落时分，暖色调，电影画质，慢动作
```

**中英混合** (推荐):
```
A silver tabby cat on white background, 柔光摄影棚打光, high detail
```

---

## 负面 Prompt 模板

```
(negative_prompt) low quality, blurry, distorted, bad anatomy,
extra limbs, deformed hands, watermark, text, signature,
dark, ugly, oversaturated, bad proportions, cropped, out of frame
```