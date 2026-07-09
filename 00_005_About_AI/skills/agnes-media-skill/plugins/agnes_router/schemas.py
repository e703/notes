"""Tool schemas for the Agnes media router plugin."""

GENERATE_IMAGE_VIA_PIC01 = {
    "name": "generate_image_via_pic01",
    "description": (
        "Generate an image through the Agnes pic_01 image service and save it "
        "safely under <workspace_root>/<project_name>/images/. Use only when "
        "the user explicitly asks to create, edit, or render an image. A concrete "
        "project_name is required."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": (
                    "Single safe project directory slug. No slashes, dots, path "
                    "traversal, or non-ASCII characters. Examples: brand_retro, "
                    "photo_project, christmas_cat_project"
                ),
            },
            "prompt": {
                "type": "string",
                "description": (
                    "Detailed visual description of the image to generate. Be specific "
                    "about subject, style, lighting, composition, and mood."
                ),
            },
            "file_name": {
                "type": "string",
                "description": (
                    "Output filename with extension (e.g. poster.png, photo_01.jpg). "
                    "Must be ASCII-only. Path components are stripped."
                ),
            },
            "size": {
                "type": "string",
                "description": "Optional image dimensions. Format: WIDTHxHEIGHT. Default: 1024x1024.",
                "default": "1024x1024",
            },
        },
        "required": ["project_name", "prompt", "file_name"],
    },
}

GENERATE_VIDEO_VIA_MOV01 = {
    "name": "generate_video_via_mov01",
    "description": (
        "Generate a video through the Agnes mov_01 video service and save it "
        "safely under <workspace_root>/<project_name>/videos/. Use only when "
        "the user explicitly asks to create video, animation, or multimedia output. "
        "A concrete project_name is required."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": (
                    "Single safe project directory slug. No slashes, dots, path "
                    "traversal, or non-ASCII characters."
                ),
            },
            "prompt": {
                "type": "string",
                "description": (
                    "Detailed video or storyboard description. Include scene changes, "
                    "camera movements, style, and duration expectations."
                ),
            },
            "file_name": {
                "type": "string",
                "description": (
                    "Output filename with extension (e.g. intro.mp4). Must be ASCII-only."
                ),
            },
        },
        "required": ["project_name", "prompt", "file_name"],
    },
}
