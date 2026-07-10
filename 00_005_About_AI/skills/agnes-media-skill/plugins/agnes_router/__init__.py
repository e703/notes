"""Agnes router plugin registration for Hermes Agent."""

from . import schemas, tools


def register(ctx):
    ctx.register_tool(
        name="generate_image_via_pic01",
        toolset="agnes_router",
        schema=schemas.GENERATE_IMAGE_VIA_PIC01,
        handler=tools.generate_image_via_pic01,
    )
    ctx.register_tool(
        name="generate_video_via_mov01",
        toolset="agnes_router",
        schema=schemas.GENERATE_VIDEO_VIA_MOV01,
        handler=tools.generate_video_via_mov01,
    )
