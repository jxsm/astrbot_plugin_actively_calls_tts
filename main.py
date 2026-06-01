from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger


class ActivelyCallsTTS(Star):
    """主动调用 TTS 语音合成插件"""

    def __init__(self, context: Context):
        super().__init__(context)

    async def terminate(self):
        """插件卸载/停用时调用"""
        pass
